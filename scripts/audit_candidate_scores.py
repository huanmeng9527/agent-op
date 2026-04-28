from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.core.query_analyzer import analyze_query
from app.core.retrieval_profiles import build_repo_aliases
from app.providers.github import GitHubProvider
from app.ranking import scorer
from app.schemas import ProviderSearchResult
from app.utils.text import unique_preserve_order


DEFAULT_BENCHMARK = Path(__file__).resolve().parents[1] / "benchmarks" / "paper_repro_benchmark.json"
DEFAULT_REPORT = Path(__file__).resolve().parents[1] / "reports" / "benchmark_report.json"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "reports" / "candidate_score_audit.md"

AUDIT_CASE_IDS = [
    "moco_2020",
    "dino_2021",
    "stylegan2_ada_2020",
    "bert_2018",
    "mask2former_2021",
    "fairseq_2019",
    "transformers_2020",
    "mmdetection_2019",
]


def _normalize_repo(repo: str | None) -> str:
    return (repo or "").strip().casefold()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _repo_key(payload: dict[str, Any]) -> str:
    return _normalize_repo(str(payload.get("full_name") or ""))


def _score_breakdown(analysis, item: ProviderSearchResult) -> dict[str, Any]:
    metadata = dict(item.metadata or {})
    text = scorer._joined_text(item)
    assets = scorer.detect_reproduction_assets(metadata, str(metadata.get("readme_text") or ""))
    repo_role = scorer.classify_repo_role(text, assets)
    tech_stack = scorer.infer_tech_stack(text)
    query_score, query_evidence = scorer._query_match_score(analysis, text)
    identity_bonus, identity_evidence = scorer._repo_name_identity_bonus(analysis, metadata, item.title)
    canonical_bonus, canonical_evidence = scorer._canonical_research_org_bonus(analysis, metadata, item.title)
    query_score = min(1.0, query_score + identity_bonus)
    asset_score, asset_evidence = scorer._asset_score(assets)
    freshness = scorer._freshness_score(metadata.get("updated_at"))
    popularity = scorer._popularity_score(metadata.get("stargazers_count"))
    risk_level, negative = scorer._risk_level(text, repo_role, assets)
    role_bonus = {
        "official_implementation": 0.10,
        "reproduction": 0.08,
        "implementation": 0.05,
        "model_zoo": 0.02,
        "demo_only": 0.01,
        "paper_collection": -0.10,
        "unknown": 0.0,
    }.get(repo_role, 0.0) + canonical_bonus
    tech_score = min(1.0, len(tech_stack) / 3)
    risk_penalty = {"low": 0.0, "medium": 0.06, "high": 0.20}[risk_level]
    raw_score = (
        query_score * 0.42
        + asset_score * 0.30
        + freshness * 0.08
        + popularity * 0.10
        + tech_score * 0.10
        + role_bonus
        - risk_penalty
    )
    cap, cap_reason = scorer._score_cap(
        metadata=metadata,
        repo_role=repo_role,
        assets=assets,
        risk_level=risk_level,
    )
    explanation = scorer.score_provider_result(analysis, item)
    return {
        "repo": _normalize_repo(str(metadata.get("full_name") or item.title)),
        "score": explanation.score,
        "raw_score": round(raw_score, 4),
        "query_score": round(query_score, 4),
        "asset_score": round(asset_score, 4),
        "freshness": round(freshness, 4),
        "popularity": round(popularity, 4),
        "tech_score": round(tech_score, 4),
        "role_bonus": round(role_bonus, 4),
        "risk_penalty": round(risk_penalty, 4),
        "cap": round(cap, 4),
        "cap_reason": cap_reason,
        "repo_role": explanation.repo_role,
        "risk_level": explanation.risk_level,
        "reference_utility": explanation.reference_utility,
        "positive_evidence": explanation.positive_evidence,
        "negative_evidence": explanation.negative_evidence,
        "assets": assets,
        "asset_evidence": asset_evidence,
        "query_evidence": unique_preserve_order([*identity_evidence, *canonical_evidence, *query_evidence]),
        "readme_present": bool(str(metadata.get("readme_text") or "").strip()),
        "root_paths_count": len(metadata.get("root_paths") or []),
        "root_paths_sample": list(metadata.get("root_paths") or [])[:8],
        "stars": metadata.get("stargazers_count"),
        "updated_at": metadata.get("updated_at"),
        "archived": bool(metadata.get("archived")),
    }


def _component_losses(official: dict[str, Any] | None, leader: dict[str, Any] | None) -> list[str]:
    if not official:
        return ["official repository could not be fetched for scoring"]
    losses: list[str] = []
    if not leader:
        return losses
    checks = [
        ("query_score", "query/paper identity match"),
        ("asset_score", "reproduction asset signals"),
        ("freshness", "freshness"),
        ("popularity", "popularity"),
        ("tech_score", "tech stack match"),
        ("role_bonus", "role/canonical bonus"),
    ]
    for key, label in checks:
        if float(leader.get(key) or 0) - float(official.get(key) or 0) >= 0.05:
            losses.append(label)
    if official.get("cap_reason"):
        losses.append(f"score cap: {official['cap_reason']}")
    if not official.get("readme_present"):
        losses.append("README missing from search-stage enrichment")
    if not official.get("root_paths_count"):
        losses.append("root tree missing from search-stage enrichment")
    return losses or ["official score is competitive; miss is mostly candidate pool/diversification"]


async def _collect_raw_candidates(
    provider: GitHubProvider,
    analysis,
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


async def _score_ranked_candidates(
    provider: GitHubProvider,
    analysis,
    items: list[dict[str, Any]],
    *,
    top_k: int,
) -> tuple[list[dict[str, Any]], dict[str, ProviderSearchResult]]:
    results = [provider._repo_to_result(repo) for repo in items if repo.get("html_url")]
    enrich_limit = min(len(results), max(top_k + 8, 12))
    enriched = await asyncio.gather(*(provider._enrich(result) for result in results[:enrich_limit]))
    ranked_results = [*enriched, *results[enrich_limit:]]
    result_by_repo = {
        _normalize_repo(str((result.metadata or {}).get("full_name") or result.title)): result
        for result in ranked_results
    }
    scored = [_score_breakdown(analysis, result) for result in ranked_results]
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored, result_by_repo


async def _fetch_scored_repo(provider: GitHubProvider, analysis, repo: str) -> dict[str, Any] | None:
    if "/" not in repo:
        return None
    owner, name = repo.split("/", 1)
    payload = await provider._fetch_repository(owner, name)
    if not payload:
        return None
    result = provider._repo_to_result(payload)
    enriched = await provider._enrich(result)
    return _score_breakdown(analysis, enriched)


def _classify_case(
    *,
    official_in_raw_pool: bool,
    official_direct_pair_attempted: bool,
    official_direct_fetched: bool,
    official_score: dict[str, Any] | None,
    leader: dict[str, Any] | None,
) -> str:
    if not official_in_raw_pool:
        if official_direct_pair_attempted and not official_direct_fetched:
            return "retrieval_pool: direct fetch attempted but did not return the labeled official repo"
        if not official_direct_pair_attempted:
            return "retrieval_pool: canonical alias does not exactly generate the labeled official repo"
        return "retrieval_pool: official repo absent before scoring"
    if official_score and official_score.get("cap_reason"):
        return "scorer_cap: official repo is present but capped below competitors"
    if official_score and leader and official_score["score"] < leader["score"]:
        return "scorer_ranking: official repo is present but loses on score components"
    return "diversification_or_identity: official repo is present but not selected into final top-k"


def _format_bool(value: bool) -> str:
    return "yes" if value else "no"


def _format_list(values: list[Any], *, empty: str = "none") -> str:
    cleaned = [str(value) for value in values if value]
    return ", ".join(f"`{value}`" for value in cleaned) if cleaned else empty


def _format_assets(assets: dict[str, bool]) -> str:
    return ", ".join(key for key, value in assets.items() if value) or "none"


def _candidate_table(candidates: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Repo | Score | Raw | Role | Cap | Assets | Readme/root | Reference utility |",
        "|---|---:|---:|---|---|---|---|---|",
    ]
    for item in candidates:
        lines.append(
            "| "
            f"`{item['repo']}` | `{item['score']:.4f}` | `{item['raw_score']:.4f}` | "
            f"`{item['repo_role']}` | `{item.get('cap_reason') or 'none'}` | "
            f"{_format_assets(item['assets'])} | "
            f"{_format_bool(item['readme_present'])}/{item['root_paths_count']} | "
            f"{'; '.join(item['reference_utility']) or 'none'} |"
        )
    return lines


def _render_markdown(audits: list[dict[str, Any]]) -> str:
    classifications: dict[str, int] = {}
    for audit in audits:
        classifications[audit["classification"]] = classifications.get(audit["classification"], 0) + 1
    lines = [
        "# Candidate Score Audit",
        "",
        "This report audits only the eight benchmark cases where a direct owner/name-style signal appears plausible but the labeled official repository is still absent from final top-3.",
        "",
        "## Scope",
        "",
        "- Main retrieval, provider, and scorer logic were not changed.",
        "- The audit script replays GitHub candidate collection, enriches the same search-stage metadata, and computes score components with existing scorer helpers.",
        "- If an official repo is absent from the replayed raw pool, its score is reported as `score_if_added` from a separate fetch for diagnosis only.",
        "",
        "## Aggregate Classification",
        "",
    ]
    for label, count in sorted(classifications.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{label}`: `{count}` cases")
    lines.extend(
        [
            "",
            "## Case Summary",
            "",
            "| Case | Official repo | Report top-3 | Official in raw pool | Direct pair | Direct fetched | Official score | Classification |",
            "|---|---|---|---|---|---|---:|---|",
        ]
    )
    for audit in audits:
        lines.append(
            "| "
            f"`{audit['id']}` | {_format_list(audit['official_repos'])} | {_format_list(audit['reported_top3'])} | "
            f"`{_format_bool(audit['official_in_raw_pool'])}` | `{_format_bool(audit['official_direct_pair_attempted'])}` | "
            f"`{_format_bool(audit['official_direct_fetched'])}` | "
            f"`{audit['official_score']['score']:.4f}` | `{audit['classification']}` |"
        )
    lines.extend(["", "## Case Details", ""])
    for audit in audits:
        official = audit["official_score"]
        lines.extend(
            [
                f"### `{audit['id']}`",
                "",
                f"- Paper: {audit['paper_title']}",
                f"- Expected official repo: {_format_list(audit['official_repos'])}",
                f"- Current benchmark top-3: {_format_list(audit['reported_top3'])}",
                f"- Replayed provider top-3: {_format_list([item['repo'] for item in audit['provider_top3']])}",
                f"- Aliases: {_format_list(audit['aliases'])}",
                f"- Official in raw candidate pool: `{_format_bool(audit['official_in_raw_pool'])}`; raw rank: `{audit['official_raw_rank'] or 'n/a'}`; source: `{audit['official_source'] or 'n/a'}`",
                f"- Official direct pair attempted: `{_format_bool(audit['official_direct_pair_attempted'])}`; direct fetched: `{_format_bool(audit['official_direct_fetched'])}`",
                f"- Official fetch error: `{audit.get('official_fetch_error') or 'none'}`",
                f"- Official score: `{official['score']:.4f}`; raw score: `{official['raw_score']:.4f}`; cap: `{official.get('cap_reason') or 'none'}`; role: `{official['repo_role']}`",
                f"- Official reference utility: {'; '.join(official['reference_utility']) or 'none'}",
                f"- Official README/root signals: readme=`{_format_bool(official['readme_present'])}`, root_paths=`{official['root_paths_count']}`",
                f"- Official loses on: {_format_list(audit['official_losses'], empty='none')}",
                f"- Diagnosis: `{audit['classification']}`",
                "",
                "Current benchmark top candidate scores:",
                "",
                *_candidate_table(audit["reported_top3_scores"]),
                "",
                "Replayed provider top candidate scores:",
                "",
                *_candidate_table(audit["provider_top3"]),
                "",
                "Official score components:",
                "",
                "| Query | Assets | Freshness | Popularity | Tech | Role bonus | Risk penalty | Cap reason |",
                "|---:|---:|---:|---:|---:|---:|---:|---|",
                f"| `{official['query_score']:.4f}` | `{official['asset_score']:.4f}` | `{official['freshness']:.4f}` | `{official['popularity']:.4f}` | `{official['tech_score']:.4f}` | `{official['role_bonus']:.4f}` | `{official['risk_penalty']:.4f}` | `{official.get('cap_reason') or 'none'}` |",
                "",
            ]
        )
    lines.extend(
        [
            "## Evidence-Backed Next Directions",
            "",
            "1. For cases where the official repo is absent before scoring, inspect canonical direct-fetch alias generation and raw candidate cutoff before touching score weights.",
            "2. For cases where the official repo is present but loses, consider a narrowly scoped scorer/cap adjustment only after comparing candidate component scores and caps.",
            "",
        ]
    )
    return "\n".join(lines)


async def audit_cases(benchmark_path: Path, report_path: Path, output_path: Path) -> list[dict[str, Any]]:
    settings = get_settings()
    if not settings.github_token:
        raise RuntimeError("GITHUB_TOKEN is required for live candidate score audit.")
    benchmark_entries = {entry["id"]: entry for entry in _load_json(benchmark_path)}
    report_details = {entry["id"]: entry for entry in _load_json(report_path).get("details", [])}
    provider = GitHubProvider()
    audits: list[dict[str, Any]] = []
    for case_id in AUDIT_CASE_IDS:
        entry = benchmark_entries[case_id]
        report_detail = report_details.get(case_id, {})
        analysis = analyze_query(
            entry["query"],
            paper_title=entry.get("paper_title"),
            task=entry.get("task"),
            source_types=["github"],
        )
        raw_items, sources, errors, canonical_pairs, direct_names, _queries = await _collect_raw_candidates(
            provider,
            analysis,
            top_k=3,
        )
        scored, _result_by_repo = await _score_ranked_candidates(provider, analysis, raw_items, top_k=3)
        provider_top3 = scored[:3]
        official_repos = [_normalize_repo(repo) for repo in entry.get("official_repos", [])]
        raw_names = [_repo_key(item) for item in raw_items]
        official_repo = official_repos[0]
        official_in_raw_pool = official_repo in raw_names
        official_raw_rank = raw_names.index(official_repo) + 1 if official_in_raw_pool else None
        official_direct_pair_attempted = any(f"{owner}/{repo}".casefold() == official_repo for owner, repo in canonical_pairs)
        official_direct_fetched = official_repo in direct_names
        official_score = next((item for item in scored if item["repo"] == official_repo), None)
        if official_score is None:
            official_score = await _fetch_scored_repo(provider, analysis, official_repo)
        official_fetch_error = provider._repo_errors.get(official_repo)
        if official_score is None:
            official_score = {
                "repo": official_repo,
                "score": 0.0,
                "raw_score": 0.0,
                "query_score": 0.0,
                "asset_score": 0.0,
                "freshness": 0.0,
                "popularity": 0.0,
                "tech_score": 0.0,
                "role_bonus": 0.0,
                "risk_penalty": 0.0,
                "cap_reason": "fetch_failed",
                "repo_role": "unknown",
                "reference_utility": [],
                "assets": {},
                "readme_present": False,
                "root_paths_count": 0,
            }
        reported_top3 = [_normalize_repo(repo) for repo in report_detail.get("retrieved") or []]
        reported_top3_scores: list[dict[str, Any]] = []
        scored_by_repo = {item["repo"]: item for item in scored}
        for repo in reported_top3:
            candidate_score = scored_by_repo.get(repo)
            if candidate_score is None:
                candidate_score = await _fetch_scored_repo(provider, analysis, repo)
            if candidate_score is not None:
                reported_top3_scores.append(candidate_score)
        leader = reported_top3_scores[0] if reported_top3_scores else provider_top3[0] if provider_top3 else None
        classification = _classify_case(
            official_in_raw_pool=official_in_raw_pool,
            official_direct_pair_attempted=official_direct_pair_attempted,
            official_direct_fetched=official_direct_fetched,
            official_score=official_score,
            leader=leader,
        )
        audits.append(
            {
                "id": case_id,
                "paper_title": entry.get("paper_title"),
                "official_repos": official_repos,
                "reported_top3": reported_top3,
                "reported_top3_scores": reported_top3_scores,
                "provider_top3": provider_top3,
                "official_in_raw_pool": official_in_raw_pool,
                "official_raw_rank": official_raw_rank,
                "official_source": sources.get(official_repo),
                "official_direct_pair_attempted": official_direct_pair_attempted,
                "official_direct_fetched": official_direct_fetched,
                "official_fetch_error": official_fetch_error,
                "official_score": official_score,
                "official_losses": _component_losses(official_score, leader),
                "classification": classification,
                "aliases": build_repo_aliases(analysis),
                "raw_pool_size": len(raw_items),
                "errors": errors,
            }
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_render_markdown(audits), encoding="utf-8")
    return audits


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit candidate-level scores for selected benchmark failures.")
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    audits = asyncio.run(audit_cases(args.benchmark, args.report, args.output))
    summary: dict[str, int] = {}
    for audit in audits:
        summary[audit["classification"]] = summary.get(audit["classification"], 0) + 1
    print(json.dumps({"cases": len(audits), "output": str(args.output), "classification": summary}, indent=2))


if __name__ == "__main__":
    main()
