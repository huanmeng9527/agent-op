from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.query_analyzer import analyze_query
from app.core.retrieval_profiles import build_repo_aliases
from app.providers.github import GitHubProvider
from app.ranking.scorer import score_provider_result
from app.schemas import ProviderSearchResult
from app.utils.text import unique_preserve_order


DEFAULT_BENCHMARK = PROJECT_ROOT / "benchmarks" / "paper_repro_benchmark.json"
DEFAULT_REPORT = PROJECT_ROOT / "reports" / "benchmark_report.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "reports" / "official_recall_drift_diagnostics.md"

TARGET_CASE_IDS = [
    "dino_2021",
    "bert_2018",
    "mask2former_2021",
    "transformers_2020",
]


def _normalize_repo(repo: str | None) -> str:
    return (repo or "").strip().casefold()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _index_by_id(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(entry.get("id")): entry for entry in entries if isinstance(entry, dict)}


def _detail_by_id(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    details = report.get("details") or []
    return _index_by_id(details if isinstance(details, list) else [])


def _repo_key(payload: dict[str, Any]) -> str:
    return _normalize_repo(str(payload.get("full_name") or ""))


def _repo_slug(repo: str) -> str:
    return _normalize_repo(repo).rsplit("/", 1)[-1].replace("_", "-")


def _owner(repo: str) -> str:
    return _normalize_repo(repo).split("/", 1)[0] if "/" in _normalize_repo(repo) else ""


def _format_bool(value: bool) -> str:
    return "yes" if value else "no"


def _format_list(values: list[Any], *, empty: str = "none") -> str:
    cleaned = [str(value) for value in values if str(value).strip()]
    return ", ".join(f"`{value}`" for value in cleaned) if cleaned else empty


def _identity_overmatches(detail: dict[str, Any], official_repos: set[str]) -> list[str]:
    overmatches: list[str] = []
    status = detail.get("provider_status") or {}
    identity_status = status.get("paper_code_identity") if isinstance(status, dict) else {}
    for repo in identity_status.get("matched_repos") or []:
        normalized = _normalize_repo(str(repo))
        if normalized and normalized not in official_repos:
            overmatches.append(normalized)
    for repo, identity in zip(detail.get("retrieved") or [], detail.get("retrieved_identity") or [], strict=False):
        if not isinstance(identity, dict) or not identity.get("source"):
            continue
        normalized = _normalize_repo(str(repo))
        if normalized and normalized not in official_repos:
            overmatches.append(normalized)
    return unique_preserve_order(overmatches)


def _collision_notes(top_candidates: list[str], official_repos: set[str]) -> list[str]:
    notes: list[str] = []
    official_slugs = {_repo_slug(repo) for repo in official_repos}
    official_stems = {slug[:-1] for slug in official_slugs if slug.endswith("s")}
    for candidate in top_candidates:
        candidate_key = _normalize_repo(candidate)
        candidate_slug = _repo_slug(candidate)
        for official in official_repos:
            official_slug = _repo_slug(official)
            official_stem = official_slug[:-1] if official_slug.endswith("s") else official_slug
            if candidate_key == official:
                continue
            if candidate_slug == official_slug:
                notes.append(f"{candidate_key} has the same slug as {official}")
            elif candidate_slug.startswith(official_slug) or official_slug in candidate_slug:
                notes.append(f"{candidate_key} prefix/contains official slug `{official_slug}`")
            elif official_stem and (candidate_slug == official_stem or candidate_slug.startswith(official_stem)):
                notes.append(f"{candidate_key} near-matches official slug `{official_slug}`")
    for candidate in top_candidates:
        candidate_slug = _repo_slug(candidate)
        if any(candidate_slug == slug for slug in official_slugs) or any(candidate_slug == stem for stem in official_stems):
            continue
    return unique_preserve_order(notes)


def _score_candidate(analysis: Any, result: ProviderSearchResult) -> dict[str, Any]:
    explanation = score_provider_result(analysis, result)
    metadata = dict(result.metadata or {})
    return {
        "repo": _normalize_repo(str(metadata.get("full_name") or result.title)),
        "score": explanation.score,
        "repo_role": explanation.repo_role,
        "cap_reason": explanation.cap_reason,
        "risk_level": explanation.risk_level,
        "positive_evidence": explanation.positive_evidence,
        "negative_evidence": explanation.negative_evidence,
        "stars": metadata.get("stargazers_count"),
        "archived": bool(metadata.get("archived")),
        "readme_present": bool(str(metadata.get("readme_text") or "").strip()),
        "root_paths_count": len(metadata.get("root_paths") or []),
    }


async def _collect_raw_candidates(
    provider: GitHubProvider,
    analysis: Any,
    *,
    top_k: int,
) -> tuple[list[dict[str, Any]], dict[str, str], list[str], list[tuple[str, str]], list[str], list[str]]:
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    sources: dict[str, str] = {}
    errors: list[str] = []
    candidate_target = min(50, max(top_k * 8, 16))
    per_query = min(20, max(top_k * 3, 10))
    canonical_pairs = provider._canonical_repo_pairs(analysis)
    direct_payloads = await provider._fetch_canonical_candidates(analysis)
    direct_names: list[str] = []
    for repo in direct_payloads:
        key = _repo_key(repo)
        if key:
            direct_names.append(key)
        if key and key not in seen:
            seen.add(key)
            sources[key] = "direct_fetch"
            items.append(repo)
    queries = provider._build_search_queries(analysis)[:12]
    for index, query in enumerate(queries, start=1):
        try:
            repos = await provider._search_repositories(query, per_page=per_query)
        except Exception as exc:
            errors.append(f"{query}: {exc}")
            continue
        for repo in repos:
            key = _repo_key(repo)
            if key and key not in seen:
                seen.add(key)
                sources[key] = f"search_query_{index}"
                items.append(repo)
        if len(items) >= candidate_target:
            break
    return items, sources, errors, canonical_pairs, direct_names, queries


async def _score_raw_candidates(
    provider: GitHubProvider,
    analysis: Any,
    items: list[dict[str, Any]],
    *,
    top_k: int,
) -> list[dict[str, Any]]:
    results = [provider._repo_to_result(repo) for repo in items if repo.get("html_url")]
    enrich_limit = min(len(results), max(top_k + 8, 12))
    enriched = await asyncio.gather(*(provider._enrich(result) for result in results[:enrich_limit]))
    ranked = [*enriched, *results[enrich_limit:]]
    scored = [_score_candidate(analysis, result) for result in ranked]
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored


async def _fetch_official(
    provider: GitHubProvider,
    analysis: Any,
    repo: str,
) -> tuple[dict[str, Any] | None, str | None]:
    if "/" not in repo:
        return None, "repo is not owner/name"
    owner, name = repo.split("/", 1)
    payload = await provider._fetch_repository(owner, name)
    if not payload:
        return None, provider._repo_errors.get(provider._repo_key(owner, name)) or "not fetched"
    result = provider._repo_to_result(payload)
    enriched = await provider._enrich(result)
    return _score_candidate(analysis, enriched), None


def _classify_root_cause(
    *,
    identity_overmatches: list[str],
    collision_notes: list[str],
    direct_pair_attempted: bool,
    direct_fetched: bool,
    official_in_raw_pool: bool,
    official_scored: dict[str, Any] | None,
    official_replay_rank: int | None,
) -> str:
    if identity_overmatches:
        return "identity_overmatching with alias/prefix collision"
    if direct_pair_attempted and not direct_fetched:
        return "direct fetch failure / GitHub live volatility"
    if not official_in_raw_pool:
        if collision_notes:
            return "GitHub live search volatility plus alias/prefix collision"
        return "GitHub live search volatility / candidate pool miss"
    if official_replay_rank and official_replay_rank <= 3:
        return "full-run drift; current replay recalls official"
    if official_scored and official_scored.get("cap_reason"):
        return "scorer/cap regression candidate"
    if official_replay_rank and official_replay_rank > 3:
        return "candidate retention/top-k boundary"
    return "candidate retention/top-k boundary"


def _next_fix(case_id: str, root_cause: str) -> str:
    if "identity_overmatching" in root_cause:
        return (
            "Tighten curated identity matching so title-token overlap cannot attach an unrelated official identity "
            "unless paper_id/arXiv/exact title agrees."
        )
    if "scorer/cap" in root_cause:
        return (
            "Design a very narrow archived-official collision check before changing anything: exact expected owner/name "
            "is present, same/prefix-slug competitors lead, and the official loses only because of archived_cap."
        )
    if case_id == "transformers_2020":
        return "Audit exact expected-owner direct fetch retention for same-slug collisions such as huggingface/transformers vs mlfoundations/transformers."
    return "Audit canonical direct-fetch retry/retention for expected official owner/name candidates under transient GitHub failures."


async def diagnose_case(entry: dict[str, Any], detail: dict[str, Any], *, top_k: int) -> dict[str, Any]:
    provider = GitHubProvider()
    analysis = analyze_query(
        entry["query"],
        paper_title=entry.get("paper_title"),
        task=entry.get("task"),
        source_types=["github"],
    )
    official_repos = {_normalize_repo(repo) for repo in entry.get("official_repos", [])}
    top_candidates = [_normalize_repo(repo) for repo in detail.get("retrieved", [])]
    identity_overmatches = _identity_overmatches(detail, official_repos)
    collision_notes = _collision_notes(top_candidates, official_repos)

    official_fetch_results: dict[str, dict[str, Any] | None] = {}
    official_fetch_errors: dict[str, str | None] = {}
    for repo in official_repos:
        score, error = await _fetch_official(provider, analysis, repo)
        official_fetch_results[repo] = score
        official_fetch_errors[repo] = error

    items, sources, errors, canonical_pairs, direct_names, queries = await _collect_raw_candidates(provider, analysis, top_k=top_k)
    raw_repos = [_repo_key(item) for item in items]
    scored = await _score_raw_candidates(provider, analysis, items, top_k=top_k)
    scored_repos = [item["repo"] for item in scored]

    official_in_raw = sorted(repo for repo in official_repos if repo in raw_repos)
    official_scored = {repo: scored[scored_repos.index(repo)] for repo in official_repos if repo in scored_repos}
    official_replay_ranks = {repo: scored_repos.index(repo) + 1 for repo in official_repos if repo in scored_repos}
    direct_pair_attempted = any(f"{owner}/{repo}".casefold() in official_repos for owner, repo in canonical_pairs)
    direct_fetched = any(repo in direct_names for repo in official_repos)
    official_absent_from_current_topk = not any(repo in top_candidates[:top_k] for repo in official_repos)
    cap_or_role_notes = []
    for repo, score in official_scored.items():
        if score.get("cap_reason"):
            cap_or_role_notes.append(f"{repo} cap={score['cap_reason']}")
        if score.get("repo_role") not in {"official_implementation", "implementation"}:
            cap_or_role_notes.append(f"{repo} role={score.get('repo_role')}")
    representative_rank = min(official_replay_ranks.values()) if official_replay_ranks else None
    representative_score = next(iter(official_scored.values()), None)
    root_cause = _classify_root_cause(
        identity_overmatches=identity_overmatches,
        collision_notes=collision_notes,
        direct_pair_attempted=direct_pair_attempted,
        direct_fetched=direct_fetched,
        official_in_raw_pool=bool(official_in_raw),
        official_scored=representative_score,
        official_replay_rank=representative_rank,
    )

    return {
        "id": entry["id"],
        "paper_title": entry.get("paper_title"),
        "expected_official_repos": sorted(official_repos),
        "current_top3": top_candidates[:3],
        "current_failure_cause": detail.get("failure_cause"),
        "current_provider_status": detail.get("provider_status") or {},
        "aliases": build_repo_aliases(analysis),
        "search_queries": queries,
        "raw_candidate_count": len(raw_repos),
        "raw_top_sample": raw_repos[:10],
        "raw_errors": errors,
        "official_in_raw_pool": bool(official_in_raw),
        "official_raw_sources": {repo: sources.get(repo) for repo in official_in_raw},
        "official_direct_pair_attempted": direct_pair_attempted,
        "official_direct_fetched": direct_fetched,
        "official_fetch_scores": official_fetch_results,
        "official_fetch_errors": official_fetch_errors,
        "official_scored": bool(official_scored),
        "official_replay_ranks": official_replay_ranks,
        "official_absent_from_current_topk": official_absent_from_current_topk,
        "official_dropped_by_replayed_topk": bool(representative_rank and representative_rank > top_k),
        "identity_overmatches": identity_overmatches,
        "collision_notes": collision_notes,
        "cap_or_role_notes": unique_preserve_order(cap_or_role_notes),
        "replayed_top5": scored[:5],
        "root_cause": root_cause,
        "next_fix": _next_fix(str(entry["id"]), root_cause),
    }


def _render_score(score: dict[str, Any] | None) -> str:
    if not score:
        return "`not scored`"
    cap = score.get("cap_reason") or "none"
    return f"`{score.get('score'):.4f}` role=`{score.get('repo_role')}` cap=`{cap}`"


def _render_replayed_table(candidates: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Rank | Repo | Score | Role | Cap | Stars | Archived |",
        "|---:|---|---:|---|---|---:|---|",
    ]
    for index, item in enumerate(candidates, start=1):
        lines.append(
            f"| {index} | `{item['repo']}` | `{item['score']:.4f}` | "
            f"`{item['repo_role']}` | `{item.get('cap_reason') or 'none'}` | "
            f"{item.get('stars') or 0} | {_format_bool(bool(item.get('archived')))} |"
        )
    return lines


def render_markdown(audits: list[dict[str, Any]], report: dict[str, Any]) -> str:
    summary = report.get("summary") or {}
    root_counts: dict[str, int] = {}
    for audit in audits:
        root_counts[audit["root_cause"]] = root_counts.get(audit["root_cause"], 0) + 1
    lines = [
        "# Official Recall Drift Diagnostics",
        "",
        "This report diagnoses only the four full-benchmark cases where the labeled official repository is absent from top-3. It does not change scorer, retrieval, provider, or identity logic.",
        "",
        "## Full Benchmark Context",
        "",
        f"- Total/evaluated: `{summary.get('total')}` / `{summary.get('evaluated')}`",
        f"- Top-1 / Top-3: `{summary.get('top1_hit_rate')}` / `{summary.get('top3_hit_rate')}`",
        f"- Official Top-1 / Top-3: `{summary.get('official_top1_hit_rate')}` / `{summary.get('official_top3_hit_rate')}`",
        f"- Distractor ranked #1: `{summary.get('distractor_top1_rate')}`",
        f"- Targeted cases: {_format_list([audit['id'] for audit in audits])}",
        "",
        "## Root Cause Summary",
        "",
    ]
    for cause, count in sorted(root_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{cause}`: `{count}`")
    lines.extend(
        [
            "",
            "## Case Summary",
            "",
            "| Case | Expected official | Current top-3 | Raw pool | Direct fetch | Scored | Replay top-k dropped | Root cause |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    for audit in audits:
        lines.append(
            f"| `{audit['id']}` | {_format_list(audit['expected_official_repos'])} | "
            f"{_format_list(audit['current_top3'])} | {_format_bool(audit['official_in_raw_pool'])} | "
            f"{_format_bool(audit['official_direct_fetched'])} | {_format_bool(audit['official_scored'])} | "
            f"{_format_bool(audit['official_dropped_by_replayed_topk'])} | `{audit['root_cause']}` |"
        )
    lines.extend(["", "## Case Details", ""])
    for audit in audits:
        fetch_score = next((score for score in audit["official_fetch_scores"].values() if score), None)
        fetch_errors = [f"{repo}: {error}" for repo, error in audit["official_fetch_errors"].items() if error]
        lines.extend(
            [
                f"### `{audit['id']}`",
                "",
                f"- Paper: {audit['paper_title']}",
                f"- Expected official repo: {_format_list(audit['expected_official_repos'])}",
                f"- Current top-3 candidates: {_format_list(audit['current_top3'])}",
                f"- Official repo in replayed raw candidate pool: `{_format_bool(audit['official_in_raw_pool'])}`; sources: `{audit['official_raw_sources'] or {}}`",
                f"- Official repo direct pair attempted: `{_format_bool(audit['official_direct_pair_attempted'])}`; direct fetched: `{_format_bool(audit['official_direct_fetched'])}`",
                f"- Official fetch/score if directly fetched: {_render_score(fetch_score)}",
                f"- Official fetch errors: {'; '.join(fetch_errors) if fetch_errors else 'none'}",
                f"- Official repo scored in replayed pool: `{_format_bool(audit['official_scored'])}`; replay ranks: `{audit['official_replay_ranks'] or {}}`",
                f"- Official absent from current full-report top-3: `{_format_bool(audit['official_absent_from_current_topk'])}`",
                f"- Official dropped by replayed top-k retention: `{_format_bool(audit['official_dropped_by_replayed_topk'])}`",
                f"- Prefix/alias collision notes: {'; '.join(audit['collision_notes']) if audit['collision_notes'] else 'none'}",
                f"- Identity candidate overmatching: {_format_list(audit['identity_overmatches'])}",
                f"- Cap/role notes: {'; '.join(audit['cap_or_role_notes']) if audit['cap_or_role_notes'] else 'none'}",
                f"- Most likely root cause: `{audit['root_cause']}`",
                f"- Next minimal fix suggestion: {audit['next_fix']}",
                "",
                "Replayed raw-pool top-5 by current scorer:",
                "",
                *_render_replayed_table(audit["replayed_top5"]),
                "",
            ]
        )
    lines.extend(
        [
            "## Recommendations",
            "",
            "- First fix DINO-style identity overmatching with a narrow identity-match guard; it is the clearest non-scoring failure and has direct evidence in the current full report.",
            "- Then inspect a very narrow archived-official collision policy for BERT and Mask2Former: exact official repo is present, but archived_cap leaves it behind prefix/same-slug variants.",
            "- Treat Transformers as live-run drift before changing logic: the targeted replay places huggingface/transformers at rank 1, so rerun targeted validation after any narrow fix.",
            "- Do not enter Papers with Code yet: these four failures are already about exact official GitHub identities drifting out of the candidate pool, not missing external project-page discovery.",
        ]
    )
    return "\n".join(lines) + "\n"


async def main_async(args: argparse.Namespace) -> None:
    benchmark = _index_by_id(_load_json(args.benchmark))
    report = _load_json(args.report)
    details = _detail_by_id(report)
    audits = []
    for case_id in TARGET_CASE_IDS:
        if case_id not in benchmark:
            raise ValueError(f"benchmark missing target case: {case_id}")
        if case_id not in details:
            raise ValueError(f"benchmark report missing target case detail: {case_id}")
        audits.append(await diagnose_case(benchmark[case_id], details[case_id], top_k=args.top_k))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_markdown(audits, report), encoding="utf-8")
    print(f"Wrote {args.output}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose four official recall drift cases without changing benchmark logic.")
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--top-k", type=int, default=3)
    return parser.parse_args()


def main() -> None:
    asyncio.run(main_async(parse_args()))


if __name__ == "__main__":
    main()
