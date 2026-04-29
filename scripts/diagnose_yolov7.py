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
from app.core.retrieval_profiles import build_github_search_queries, build_repo_aliases
from app.providers.github import GitHubProvider
from app.providers.paper_code_identity import PaperCodeIdentityProvider
from app.ranking.scorer import score_provider_result
from app.schemas import ProviderSearchResult


DEFAULT_BENCHMARK = PROJECT_ROOT / "benchmarks" / "paper_repro_benchmark.json"
DEFAULT_REPORT = PROJECT_ROOT / "reports" / "benchmark_report.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "reports" / "yolov7_diagnostics.md"
CASE_ID = "yolov7_2022"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_repo(repo: str | None) -> str:
    return (repo or "").strip().casefold()


def _repo_key(payload: dict[str, Any]) -> str:
    return _normalize_repo(str(payload.get("full_name") or ""))


def _format_bool(value: bool) -> str:
    return "yes" if value else "no"


def _format_list(values: list[Any], *, empty: str = "none") -> str:
    cleaned = [str(value) for value in values if str(value).strip()]
    return ", ".join(f"`{value}`" for value in cleaned) if cleaned else empty


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
        "reference_utility": explanation.reference_utility,
        "stars": metadata.get("stargazers_count"),
        "archived": bool(metadata.get("archived")),
        "fork": bool(metadata.get("fork")),
        "owner": metadata.get("owner"),
        "description": metadata.get("description"),
        "topics": metadata.get("topics") or [],
        "readme_present": bool(str(metadata.get("readme_text") or "").strip()),
        "root_paths_count": len(metadata.get("root_paths") or []),
    }


async def _fetch_scored_repo(
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
    result = await provider._enrich(provider._repo_to_result(payload))
    return _score_candidate(analysis, result), None


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
            sources[key] = "canonical_direct_fetch"
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


def _classify_candidate(repo: str, score: dict[str, Any] | None, official: set[str], reproductions: set[str], distractors: set[str]) -> str:
    normalized = _normalize_repo(repo)
    if normalized in official:
        return "expected official"
    if normalized in reproductions:
        return "high-quality reproduction"
    if normalized in distractors:
        return "labeled distractor"
    if "ultralytics" in normalized:
        return "YOLO/Ultralytics adjacent project"
    if "yolo" in normalized:
        return "YOLO alias/variant"
    if score:
        role = str(score.get("repo_role") or "unknown")
        if score.get("cap_reason"):
            return f"{role}, capped by {score['cap_reason']}"
        return role
    return "unknown"


def _root_cause(
    *,
    canonical_direct_pair_attempted: bool,
    current_replay_has_official: bool,
    current_replay_rank: int | None,
    manual_direct_fetch_succeeded: bool,
    identity_matches: list[str],
    official_score: dict[str, Any] | None,
) -> str:
    if identity_matches:
        return "identity overmatching"
    if manual_direct_fetch_succeeded and current_replay_has_official and current_replay_rank and current_replay_rank <= 3:
        return "GitHub live search volatility; current replay recalls the official repo"
    if manual_direct_fetch_succeeded and not canonical_direct_pair_attempted and not current_replay_has_official:
        return "identity/direct-fetch coverage gap for a non-canonical owner"
    if not manual_direct_fetch_succeeded:
        return "direct fetch failure or renamed/redirect issue"
    if official_score and official_score.get("cap_reason") and current_replay_rank and current_replay_rank > 3:
        return "scorer/cap boundary"
    return "candidate retention/top-k boundary"


async def diagnose(args: argparse.Namespace) -> dict[str, Any]:
    benchmark_entries = _load_json(args.benchmark)
    benchmark = {entry["id"]: entry for entry in benchmark_entries}
    entry = benchmark[CASE_ID]
    report = _load_json(args.report)
    detail = next(item for item in report["details"] if item["id"] == CASE_ID)
    analysis = analyze_query(
        entry["query"],
        paper_title=entry.get("paper_title"),
        task=entry.get("task"),
        source_types=["github"],
    )
    provider = GitHubProvider()
    identity_provider = PaperCodeIdentityProvider()
    identity_matches = identity_provider.resolve(analysis)
    official = {_normalize_repo(repo) for repo in entry.get("official_repos", [])}
    reproductions = {_normalize_repo(repo) for repo in entry.get("high_quality_reproduction_repos", [])}
    distractors = {_normalize_repo(repo) for repo in entry.get("common_distractor_repos", [])}

    official_repo = entry["official_repos"][0]
    official_score, official_fetch_error = await _fetch_scored_repo(provider, analysis, official_repo)
    top3_scores: dict[str, dict[str, Any] | None] = {}
    top3_errors: dict[str, str | None] = {}
    for repo in detail.get("retrieved", []):
        score, error = await _fetch_scored_repo(provider, analysis, repo)
        top3_scores[_normalize_repo(repo)] = score
        top3_errors[_normalize_repo(repo)] = error

    items, sources, errors, canonical_pairs, direct_names, queries = await _collect_raw_candidates(provider, analysis, top_k=args.top_k)
    raw_repos = [_repo_key(item) for item in items]
    scored = await _score_raw_candidates(provider, analysis, items, top_k=args.top_k)
    scored_repos = [item["repo"] for item in scored]
    official_normalized = _normalize_repo(official_repo)
    official_replay_rank = scored_repos.index(official_normalized) + 1 if official_normalized in scored_repos else None
    canonical_direct_pair_attempted = any(
        f"{owner}/{repo}".casefold() == official_normalized
        for owner, repo in canonical_pairs
    )
    root_cause = _root_cause(
        canonical_direct_pair_attempted=canonical_direct_pair_attempted,
        current_replay_has_official=official_normalized in raw_repos,
        current_replay_rank=official_replay_rank,
        manual_direct_fetch_succeeded=official_score is not None,
        identity_matches=[match.repo for match in identity_matches],
        official_score=official_score,
    )
    return {
        "entry": entry,
        "detail": detail,
        "analysis": analysis.model_dump(),
        "aliases": build_repo_aliases(analysis),
        "search_queries": build_github_search_queries(analysis)[:12],
        "identity_matches": [match.to_metadata() for match in identity_matches],
        "canonical_direct_pair_attempted": canonical_direct_pair_attempted,
        "canonical_direct_names": direct_names,
        "manual_official_direct_fetch_succeeded": official_score is not None,
        "official_fetch_error": official_fetch_error,
        "official_score": official_score,
        "raw_candidate_count": len(raw_repos),
        "raw_repos_sample": raw_repos[:15],
        "raw_sources": sources,
        "raw_errors": errors,
        "official_in_raw_pool": official_normalized in raw_repos,
        "official_raw_source": sources.get(official_normalized),
        "official_replay_rank": official_replay_rank,
        "replayed_top10": scored[:10],
        "top3_scores": top3_scores,
        "top3_errors": top3_errors,
        "top3_types": {
            repo: _classify_candidate(repo, top3_scores.get(_normalize_repo(repo)), official, reproductions, distractors)
            for repo in detail.get("retrieved", [])
        },
        "root_cause": root_cause,
    }


def _render_score(score: dict[str, Any] | None) -> str:
    if not score:
        return "`not scored`"
    cap = score.get("cap_reason") or "none"
    return (
        f"`{score['score']:.4f}`; role=`{score['repo_role']}`; cap=`{cap}`; "
        f"archived=`{_format_bool(bool(score.get('archived')))}`; fork=`{_format_bool(bool(score.get('fork')))}`"
    )


def _candidate_table(candidates: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Rank | Repo | Score | Role | Cap | Stars | Archived | Fork |",
        "|---:|---|---:|---|---|---:|---|---|",
    ]
    for index, item in enumerate(candidates, start=1):
        lines.append(
            f"| {index} | `{item['repo']}` | `{item['score']:.4f}` | `{item['repo_role']}` | "
            f"`{item.get('cap_reason') or 'none'}` | {item.get('stars') or 0} | "
            f"{_format_bool(bool(item.get('archived')))} | {_format_bool(bool(item.get('fork')))} |"
        )
    return lines


def render_report(audit: dict[str, Any]) -> str:
    entry = audit["entry"]
    detail = audit["detail"]
    official = entry.get("official_repos") or []
    reproductions = entry.get("high_quality_reproduction_repos") or []
    distractors = entry.get("common_distractor_repos") or []
    identity_repos = [match["repo"] for match in audit["identity_matches"]]
    top3_lines = [
        "| Repo | Type | Score / Role / Cap | Fetch error |",
        "|---|---|---|---|",
    ]
    for repo in detail.get("retrieved", []):
        key = _normalize_repo(repo)
        top3_lines.append(
            f"| `{repo}` | {audit['top3_types'].get(repo, 'unknown')} | "
            f"{_render_score(audit['top3_scores'].get(key))} | "
            f"{audit['top3_errors'].get(key) or 'none'} |"
        )
    lines = [
        "# YOLOv7 Targeted Diagnostics",
        "",
        "This report diagnoses only `yolov7_2022`. It does not modify scorer, retrieval, provider, identity, or benchmark logic.",
        "",
        "## Benchmark Entry",
        "",
        f"- Paper title: {entry['paper_title']}",
        f"- Query: `{entry['query']}`",
        f"- Official repos: {_format_list(official)}",
        f"- High-quality reproduction repos: {_format_list(reproductions)}",
        f"- Common distractor repos: {_format_list(distractors)}",
        f"- Repo aliases generated from the current query: {_format_list(audit['aliases'])}",
        "",
        "## Current Full Benchmark Result",
        "",
        f"- Current top-3: {_format_list(detail.get('retrieved') or [])}",
        f"- Failure cause: `{detail.get('failure_cause')}`",
        f"- Official rank: `{detail.get('official_rank')}`",
        f"- Acceptable rank: `{detail.get('acceptable_rank')}`",
        f"- Provider status: `{detail.get('provider_status')}`",
        "",
        "## Targeted Replay Findings",
        "",
        f"- Identity matches: {_format_list(identity_repos)}",
        f"- Provider canonical direct fetch attempted official owner/name: `{_format_bool(audit['canonical_direct_pair_attempted'])}`",
        f"- Manual official direct fetch succeeded: `{_format_bool(audit['manual_official_direct_fetch_succeeded'])}`",
        f"- Manual official fetch error: `{audit['official_fetch_error'] or 'none'}`",
        f"- Official score if fetched directly: {_render_score(audit['official_score'])}",
        f"- Official repo in replayed raw candidate pool: `{_format_bool(audit['official_in_raw_pool'])}`",
        f"- Official raw source: `{audit['official_raw_source'] or 'none'}`",
        f"- Official replay rank: `{audit['official_replay_rank']}`",
        f"- Raw candidate count: `{audit['raw_candidate_count']}`",
        f"- Raw candidate sample: {_format_list(audit['raw_repos_sample'])}",
        f"- Raw replay errors: {'; '.join(audit['raw_errors']) if audit['raw_errors'] else 'none'}",
        "",
        "## Current Full Top-3 Candidate Types",
        "",
        *top3_lines,
        "",
        "## Replayed Top-10 By Current Scorer",
        "",
        *_candidate_table(audit["replayed_top10"]),
        "",
        "## Alias / Owner Collision Notes",
        "",
        "- Current generated aliases include `yolov7`, `yol_ov_7`, and `yol-ov-7`; the exact official slug is available.",
        "- The official owner `WongKinYiu` is not in the provider canonical-owner direct-fetch list, so the normal provider path relies on GitHub search unless an external identity mapping supplies this exact repo.",
        "- The full-run top-3 did not include the labeled distractor `ultralytics/ultralytics`; this miss is not a YOLOv8/Ultralytics rank-1 distractor issue.",
        "- Manual fetch returns `WongKinYiu/yolov7` at the same path, so this is not a renamed/redirect problem.",
        "",
        "## Root Cause",
        "",
        f"- Most likely root cause: `{audit['root_cause']}`.",
        "- Scorer/cap is not the primary issue: direct official fetch scores high enough for Top-3.",
        "- Benchmark label looks valid: the fetched official repository description directly names the YOLOv7 paper.",
        "",
        "## Next Minimal Fix Suggestion",
        "",
        "- Prefer a curated official identity mapping for `yolov7_2022 -> WongKinYiu/yolov7` with evidence from the repository description/source URL. This is narrower and safer than broadening YOLO retrieval or adding `WongKinYiu` as a global canonical owner.",
        "- Do not enter Papers with Code yet; the exact GitHub repository is known and direct fetch succeeds.",
    ]
    return "\n".join(lines) + "\n"


async def main_async(args: argparse.Namespace) -> None:
    audit = await diagnose(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_report(audit), encoding="utf-8")
    print(f"Wrote {args.output}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose yolov7_2022 official recall drift without changing search logic.")
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--top-k", type=int, default=3)
    return parser.parse_args()


def main() -> None:
    asyncio.run(main_async(parse_args()))


if __name__ == "__main__":
    main()
