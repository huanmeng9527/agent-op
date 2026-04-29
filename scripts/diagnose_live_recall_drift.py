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
from app.providers.paper_code_identity import PaperCodeIdentityProvider
from app.ranking import scorer
from app.schemas import ProviderSearchResult
from app.tools.paper_tools import search_paper_repos_tool
from app.utils.text import truncate_text, unique_preserve_order


DEFAULT_BENCHMARK = PROJECT_ROOT / "benchmarks" / "paper_repro_benchmark.json"
DEFAULT_REPORT = PROJECT_ROOT / "reports" / "benchmark_report.json"
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "reports" / "live_recall_drift_diagnostics.json"
DEFAULT_MD_OUTPUT = PROJECT_ROOT / "reports" / "live_recall_drift_diagnostics.md"

TARGET_CASE_IDS = [
    "nerf_2020",
    "simclr_2020",
    "alphafold_2021",
    "raft_2020",
    "monodepth2_2019",
]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_repo(repo: str | None) -> str:
    return (repo or "").strip().casefold()


def _index_by_id(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(entry.get("id")): entry for entry in entries if isinstance(entry, dict)}


def _detail_by_id(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    details = report.get("details") or []
    return _index_by_id(details if isinstance(details, list) else [])


def _repo_key(payload: dict[str, Any]) -> str:
    return _normalize_repo(str(payload.get("full_name") or ""))


def _format_bool(value: bool) -> str:
    return "yes" if value else "no"


def _format_list(values: list[Any], *, empty: str = "none") -> str:
    cleaned = [str(value) for value in values if str(value).strip()]
    return ", ".join(f"`{value}`" for value in cleaned) if cleaned else empty


def _raw_repo_summary(payload: dict[str, Any], *, rank: int | None = None, source: str | None = None) -> dict[str, Any]:
    return {
        "rank": rank,
        "source": source,
        "full_name": _repo_key(payload),
        "description": truncate_text(str(payload.get("description") or ""), 220),
        "stars": payload.get("stargazers_count"),
        "archived": bool(payload.get("archived")),
        "fork": bool(payload.get("fork")),
        "owner": ((payload.get("owner") or {}).get("login") if isinstance(payload.get("owner"), dict) else None),
        "topics": list(payload.get("topics") or [])[:10],
        "updated_at": payload.get("updated_at"),
        "html_url": payload.get("html_url"),
    }


def _score_breakdown(analysis: Any, item: ProviderSearchResult) -> dict[str, Any]:
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
    query_signals = unique_preserve_order([*identity_evidence, *canonical_evidence, *query_evidence])
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
        "value_level": explanation.value_level,
        "confidence_level": explanation.confidence_level,
        "tech_stack": explanation.tech_stack,
        "assets": assets,
        "query_evidence": query_signals,
        "asset_evidence": asset_evidence,
        "positive_evidence": explanation.positive_evidence,
        "negative_evidence": unique_preserve_order([*negative, *explanation.negative_evidence]),
        "matched_signals": unique_preserve_order([*query_signals, *asset_evidence, *explanation.positive_evidence]),
        "reference_utility": explanation.reference_utility,
        "stars": metadata.get("stargazers_count"),
        "description": metadata.get("description"),
        "archived": bool(metadata.get("archived")),
        "readme_present": bool(str(metadata.get("readme_text") or "").strip()),
        "root_paths_count": len(metadata.get("root_paths") or []),
        "root_paths_sample": list(metadata.get("root_paths") or [])[:8],
    }


async def _fetch_scored_repo(
    provider: GitHubProvider,
    analysis: Any,
    repo: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, str | None]:
    if "/" not in repo:
        return None, None, "repo is not owner/name"
    owner, name = repo.split("/", 1)
    payload = await provider._fetch_repository(owner, name)
    if not payload:
        return None, None, provider._repo_errors.get(provider._repo_key(owner, name)) or "not fetched"
    result = await provider._enrich(provider._repo_to_result(payload))
    return _raw_repo_summary(payload), _score_breakdown(analysis, result), None


async def _collect_provider_debug(
    provider: GitHubProvider,
    analysis: Any,
    official_repos: set[str],
    *,
    top_k: int,
) -> dict[str, Any]:
    seen: set[str] = set()
    provider_pool: list[dict[str, Any]] = []
    provider_pool_sources: dict[str, str] = {}
    query_results: list[dict[str, Any]] = []
    query_errors: list[str] = []
    candidate_target = min(50, max(top_k * 8, 16))
    per_query = min(20, max(top_k * 3, 10))

    canonical_pairs = provider._canonical_repo_pairs(analysis)
    direct_payloads = await provider._fetch_canonical_candidates(analysis)
    direct_names: list[str] = []
    for payload in direct_payloads:
        key = _repo_key(payload)
        if key:
            direct_names.append(key)
        if key and key not in seen:
            seen.add(key)
            provider_pool_sources[key] = "canonical_direct_fetch"
            provider_pool.append(payload)

    stopped_after_query: int | None = None
    queries = provider._build_search_queries(analysis)[:12]
    for query_index, query in enumerate(queries, start=1):
        result: dict[str, Any] = {
            "index": query_index,
            "query": query,
            "per_page": per_query,
            "included_in_provider_pool": stopped_after_query is None,
            "error": None,
            "official_present": False,
            "official_rank": None,
            "candidates": [],
        }
        try:
            repos = await provider._search_repositories(query, per_page=per_query)
        except Exception as exc:
            result["error"] = str(exc)
            query_errors.append(f"{query}: {exc}")
            query_results.append(result)
            continue
        for rank, payload in enumerate(repos, start=1):
            key = _repo_key(payload)
            if key in official_repos and result["official_rank"] is None:
                result["official_present"] = True
                result["official_rank"] = rank
            result["candidates"].append(_raw_repo_summary(payload, rank=rank, source=f"search_query_{query_index}"))
            if stopped_after_query is None and key and key not in seen:
                seen.add(key)
                provider_pool_sources[key] = f"search_query_{query_index}"
                provider_pool.append(payload)
        query_results.append(result)
        if stopped_after_query is None and len(provider_pool) >= candidate_target:
            stopped_after_query = query_index

    return {
        "queries": queries,
        "per_query": per_query,
        "candidate_target": candidate_target,
        "canonical_pairs": [f"{owner}/{repo}".casefold() for owner, repo in canonical_pairs],
        "canonical_direct_names": direct_names,
        "provider_pool": provider_pool,
        "provider_pool_sources": provider_pool_sources,
        "provider_stopped_after_query": stopped_after_query,
        "query_results": query_results,
        "query_errors": query_errors,
    }


async def _score_provider_pool(
    provider: GitHubProvider,
    analysis: Any,
    items: list[dict[str, Any]],
    *,
    top_k: int,
) -> list[dict[str, Any]]:
    results = [provider._repo_to_result(payload) for payload in items if payload.get("html_url")]
    enrich_limit = min(len(results), max(top_k + 8, 12))
    enriched = await asyncio.gather(*(provider._enrich(result) for result in results[:enrich_limit]))
    ranked_results = [*enriched, *results[enrich_limit:]]
    scored = [_score_breakdown(analysis, result) for result in ranked_results]
    scored.sort(key=lambda item: item["score"], reverse=True)
    for rank, item in enumerate(scored, start=1):
        item["rank"] = rank
    return scored


async def _provider_search_results(provider: GitHubProvider, analysis: Any, *, top_k: int) -> list[dict[str, Any]]:
    results = await provider.search(analysis, top_k=top_k)
    output: list[dict[str, Any]] = []
    for rank, result in enumerate(results, start=1):
        scored = _score_breakdown(analysis, result)
        scored["rank"] = rank
        output.append(scored)
    return output


async def _service_results(entry: dict[str, Any], *, top_k: int) -> dict[str, Any]:
    output = await search_paper_repos_tool(
        query=entry["query"],
        paper_title=entry.get("paper_title"),
        task=entry.get("task"),
        top_k=top_k,
        include_unofficial=True,
    )
    results = []
    for rank, item in enumerate(output.results, start=1):
        results.append(
            {
                "rank": rank,
                "repo": _normalize_repo(item.repo),
                "title": item.title,
                "score": item.score,
                "repo_role": item.repo_role,
                "cap_reason": item.cap_reason,
                "identity_source": item.identity_source,
                "identity_confidence": item.identity_confidence,
                "identity_type": item.identity_type,
                "identity_evidence": item.identity_evidence,
                "positive_evidence": item.positive_evidence,
                "negative_evidence": item.negative_evidence,
                "stars": item.stars,
                "archived": bool((item.metadata or {}).get("archived")),
            }
        )
    return {
        "query_analysis": output.query_analysis.model_dump(),
        "provider_status": output.provider_status,
        "warnings": output.warnings,
        "results": results,
    }


def _classify(
    *,
    full_detail: dict[str, Any],
    official_repos: set[str],
    direct_fetch: dict[str, Any],
    provider_debug: dict[str, Any],
    scored_pool: list[dict[str, Any]],
    provider_search: list[dict[str, Any]],
    service: dict[str, Any],
) -> tuple[str, list[str]]:
    labels: list[str] = []
    query_present = any(bool(query["official_present"]) for query in provider_debug["query_results"])
    provider_pool_repos = {_repo_key(payload) for payload in provider_debug["provider_pool"]}
    scored_repos = [item["repo"] for item in scored_pool]
    provider_top_repos = [item["repo"] for item in provider_search]
    service_top_repos = [item["repo"] for item in service["results"]]
    direct_success = any(item.get("fetch_succeeded") for item in direct_fetch.values())
    direct_identity_mismatch = any(item.get("identity_mismatch") for item in direct_fetch.values())
    official_in_provider_pool = bool(official_repos & provider_pool_repos)
    official_scored_ranks = [
        scored_repos.index(repo) + 1
        for repo in official_repos
        if repo in scored_repos
    ]
    provider_top_hit = bool(official_repos & set(provider_top_repos[:3]))
    service_top_hit = bool(official_repos & set(service_top_repos[:3]))
    full_top_hit = bool(full_detail.get("official_top3_hit"))

    if direct_identity_mismatch:
        labels.append("identity_mismatch")
    if query_present and not official_in_provider_pool:
        labels.append("filter_or_dedup_loss")
    if official_scored_ranks and min(official_scored_ranks) > 3:
        labels.append("scoring_or_ranking_loss")
    if not query_present and not official_in_provider_pool:
        labels.append("provider_recall_miss")
    if not full_top_hit and (provider_top_hit or service_top_hit or (official_scored_ranks and min(official_scored_ranks) <= 3)):
        labels.append("live_search_drift")
    if direct_success and not query_present and not official_in_provider_pool:
        labels.append("live_search_drift")

    if "identity_mismatch" in labels:
        primary = "identity_mismatch"
    elif "filter_or_dedup_loss" in labels:
        primary = "filter_or_dedup_loss"
    elif "scoring_or_ranking_loss" in labels:
        primary = "scoring_or_ranking_loss"
    elif "provider_recall_miss" in labels and "live_search_drift" in labels:
        primary = "provider_recall_miss + live_search_drift"
    elif "provider_recall_miss" in labels:
        primary = "provider_recall_miss"
    elif "live_search_drift" in labels:
        primary = "live_search_drift"
    else:
        primary = "needs_manual_review"
    return primary, unique_preserve_order(labels)


def _next_step(primary: str, case_id: str) -> str:
    if "identity_mismatch" in primary:
        return "Check expected owner/name versus GitHub canonical path and preserve aliases if GitHub redirects."
    if "filter_or_dedup_loss" in primary:
        return "Inspect provider early-stop/dedup retention for the query where the official repo appears before changing scoring."
    if "scoring_or_ranking_loss" in primary:
        return "Audit score components for the official repo versus leading candidates; do not change scorer until the loss is reproduced in targeted replay."
    if "provider_recall_miss" in primary:
        return (
            "First verify manual direct fetch evidence; if the repo is stable and benchmark-official, prefer a narrow curated official identity "
            f"for `{case_id}` over broad retrieval changes."
        )
    if primary == "live_search_drift":
        return "Rerun targeted validation and compare raw query positions; this may not need a logic change."
    return "Repeat targeted replay with raw GitHub query capture and inspect provider errors."


async def diagnose_case(entry: dict[str, Any], full_detail: dict[str, Any], *, top_k: int) -> dict[str, Any]:
    analysis = analyze_query(
        entry["query"],
        paper_title=entry.get("paper_title"),
        task=entry.get("task"),
        source_types=["github"],
    )
    provider = GitHubProvider()
    identity_provider = PaperCodeIdentityProvider()
    identity_matches = identity_provider.resolve(analysis)
    official_repos = {_normalize_repo(repo) for repo in entry.get("official_repos", [])}

    direct_fetch: dict[str, Any] = {}
    for repo in sorted(official_repos):
        raw, score, error = await _fetch_scored_repo(provider, analysis, repo)
        aliases = [repo]
        if raw and raw.get("full_name"):
            aliases.append(str(raw["full_name"]))
        direct_fetch[repo] = {
            "repo": repo,
            "fetch_succeeded": raw is not None,
            "fetch_error": error,
            "raw": raw,
            "score_breakdown": score,
            "canonical_full_name": (raw or {}).get("full_name"),
            "identity_mismatch": bool(raw and repo not in {_normalize_repo(value) for value in aliases}),
        }

    provider_debug = await _collect_provider_debug(provider, analysis, official_repos, top_k=top_k)
    scored_pool = await _score_provider_pool(provider, analysis, provider_debug["provider_pool"], top_k=top_k)
    provider_search = await _provider_search_results(provider, analysis, top_k=top_k)
    service = await _service_results(entry, top_k=top_k)
    primary, labels = _classify(
        full_detail=full_detail,
        official_repos=official_repos,
        direct_fetch=direct_fetch,
        provider_debug=provider_debug,
        scored_pool=scored_pool,
        provider_search=provider_search,
        service=service,
    )

    provider_pool_repos = [_repo_key(payload) for payload in provider_debug["provider_pool"]]
    scored_repos = [item["repo"] for item in scored_pool]
    query_presence = [
        {
            "query_index": item["index"],
            "query": item["query"],
            "official_present": item["official_present"],
            "official_rank": item["official_rank"],
            "included_in_provider_pool": item["included_in_provider_pool"],
        }
        for item in provider_debug["query_results"]
    ]
    return {
        "case_id": entry["id"],
        "paper_title": entry.get("paper_title"),
        "query": entry.get("query"),
        "task": entry.get("task"),
        "official_repos": sorted(official_repos),
        "high_quality_reproduction_repos": [_normalize_repo(repo) for repo in entry.get("high_quality_reproduction_repos", [])],
        "common_distractor_repos": [_normalize_repo(repo) for repo in entry.get("common_distractor_repos", [])],
        "benchmark_full_result": {
            "failure_cause": full_detail.get("failure_cause"),
            "top3": full_detail.get("retrieved") or [],
            "official_rank": full_detail.get("official_rank"),
            "acceptable_rank": full_detail.get("acceptable_rank"),
            "official_top3_hit": bool(full_detail.get("official_top3_hit")),
            "provider_status": full_detail.get("provider_status") or {},
        },
        "analysis": analysis.model_dump(),
        "aliases": build_repo_aliases(analysis),
        "identity_matches": [match.to_metadata() for match in identity_matches],
        "direct_fetch": direct_fetch,
        "search_queries": provider_debug["queries"],
        "query_presence": query_presence,
        "query_results": provider_debug["query_results"],
        "provider_pool": {
            "candidate_target": provider_debug["candidate_target"],
            "per_query": provider_debug["per_query"],
            "stopped_after_query": provider_debug["provider_stopped_after_query"],
            "candidate_count": len(provider_pool_repos),
            "official_in_provider_pool": bool(official_repos & set(provider_pool_repos)),
            "official_sources": {
                repo: provider_debug["provider_pool_sources"].get(repo)
                for repo in sorted(official_repos)
                if repo in provider_debug["provider_pool_sources"]
            },
            "canonical_direct_pair_attempted": bool(official_repos & set(provider_debug["canonical_pairs"])),
            "canonical_direct_names": provider_debug["canonical_direct_names"],
            "candidates": [
                _raw_repo_summary(payload, rank=rank, source=provider_debug["provider_pool_sources"].get(_repo_key(payload)))
                for rank, payload in enumerate(provider_debug["provider_pool"], start=1)
            ],
            "errors": provider_debug["query_errors"],
        },
        "scored_pool": {
            "official_scored": bool(official_repos & set(scored_repos)),
            "official_ranks": {
                repo: scored_repos.index(repo) + 1
                for repo in sorted(official_repos)
                if repo in scored_repos
            },
            "top10": scored_pool[:10],
        },
        "github_provider_topk": provider_search,
        "service_topk": service,
        "classification": {
            "primary": primary,
            "labels": labels,
            "next_minimal_step": _next_step(primary, str(entry["id"])),
        },
    }


def _score_fragment(score: dict[str, Any] | None) -> str:
    if not score:
        return "`not scored`"
    return (
        f"`{score.get('score'):.4f}` raw=`{score.get('raw_score'):.4f}` "
        f"role=`{score.get('repo_role')}` cap=`{score.get('cap_reason') or 'none'}`"
    )


def _candidate_table(candidates: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Rank | Repo | Score | Raw | Role | Cap | Stars | Archived | Signals |",
        "|---:|---|---:|---:|---|---|---:|---|---|",
    ]
    for item in candidates:
        lines.append(
            f"| {item.get('rank')} | `{item.get('repo')}` | `{item.get('score'):.4f}` | "
            f"`{item.get('raw_score'):.4f}` | `{item.get('repo_role')}` | `{item.get('cap_reason') or 'none'}` | "
            f"{item.get('stars') or 0} | {_format_bool(bool(item.get('archived')))} | "
            f"{'; '.join((item.get('matched_signals') or [])[:3]) or 'none'} |"
        )
    return lines


def _raw_table(candidates: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Rank | Source | Repo | Stars | Archived | Description |",
        "|---:|---|---|---:|---|---|",
    ]
    for item in candidates[:12]:
        lines.append(
            f"| {item.get('rank')} | `{item.get('source') or 'unknown'}` | `{item.get('full_name')}` | "
            f"{item.get('stars') or 0} | {_format_bool(bool(item.get('archived')))} | "
            f"{str(item.get('description') or '').replace('|', '/')} |"
        )
    return lines


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    classification_counts = summary["classification_counts"]
    lines = [
        "# Live Recall Drift Diagnostics",
        "",
        "This targeted diagnostic report replays only the five current `official_repo_not_recalled` / `expected_repo_not_recalled` cases. It does not modify scorer, retrieval, provider, identity, or benchmark logic.",
        "",
        "## Scope",
        "",
        f"- Target cases: {_format_list(summary['target_case_ids'])}",
        f"- Source full benchmark: Top-1 `{summary['benchmark_summary'].get('top1_hit_rate')}`, Top-3 `{summary['benchmark_summary'].get('top3_hit_rate')}`, Official Top-3 `{summary['benchmark_summary'].get('official_top3_hit_rate')}`",
        f"- Provider failed / rate limited in source report: `{summary['benchmark_summary'].get('provider_failed')}` / `{summary['benchmark_summary'].get('rate_limited')}`",
        "",
        "## Classification Summary",
        "",
    ]
    for classification, count in sorted(classification_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{classification}`: `{count}`")
    lines.extend(
        [
            "",
            "## Case Summary",
            "",
            "| Case | Expected official | Full top-3 | Direct fetch | Raw query hit | Provider pool | Scored rank | Current service top-3 | Classification |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for case in report["cases"]:
        direct_ok = any(item.get("fetch_succeeded") for item in case["direct_fetch"].values())
        raw_hit = any(item["official_present"] for item in case["query_presence"])
        provider_pool_hit = case["provider_pool"]["official_in_provider_pool"]
        scored_ranks = case["scored_pool"]["official_ranks"]
        service_top3 = [item["repo"] for item in case["service_topk"]["results"]]
        lines.append(
            f"| `{case['case_id']}` | {_format_list(case['official_repos'])} | "
            f"{_format_list(case['benchmark_full_result']['top3'])} | {_format_bool(direct_ok)} | "
            f"{_format_bool(raw_hit)} | {_format_bool(provider_pool_hit)} | `{scored_ranks or {}}` | "
            f"{_format_list(service_top3)} | `{case['classification']['primary']}` |"
        )
    lines.extend(["", "## Case Details", ""])
    for case in report["cases"]:
        direct_scores = [
            value.get("score_breakdown")
            for value in case["direct_fetch"].values()
            if value.get("score_breakdown")
        ]
        query_hits = [
            f"q{item['query_index']} rank {item['official_rank']}"
            for item in case["query_presence"]
            if item["official_present"]
        ]
        provider_candidates = case["provider_pool"]["candidates"]
        service_results = case["service_topk"]["results"]
        lines.extend(
            [
                f"### `{case['case_id']}`",
                "",
                f"- Paper title: {case['paper_title']}",
                f"- Expected official repo: {_format_list(case['official_repos'])}",
                f"- Full benchmark top-3: {_format_list(case['benchmark_full_result']['top3'])}",
                f"- Search queries: {_format_list(case['search_queries'])}",
                f"- Generated aliases: {_format_list(case['aliases'])}",
                f"- Identity matches: {_format_list([match['repo'] for match in case['identity_matches']])}",
                f"- Official appears in raw GitHub query results: `{_format_bool(bool(query_hits))}` ({'; '.join(query_hits) if query_hits else 'none'})",
                f"- Official in provider-considered pool: `{_format_bool(case['provider_pool']['official_in_provider_pool'])}`; sources: `{case['provider_pool']['official_sources'] or {}}`",
                f"- Official scored ranks in replayed provider pool: `{case['scored_pool']['official_ranks'] or {}}`",
                f"- Direct official fetch score: {_score_fragment(direct_scores[0] if direct_scores else None)}",
                f"- Current targeted service top-3: {_format_list([item['repo'] for item in service_results])}",
                f"- Classification: `{case['classification']['primary']}`; labels: {_format_list(case['classification']['labels'])}",
                f"- Next minimal step: {case['classification']['next_minimal_step']}",
                "",
                "Provider-considered raw candidates:",
                "",
                *_raw_table(provider_candidates),
                "",
                "Replayed scored provider-pool top-10:",
                "",
                *_candidate_table(case["scored_pool"]["top10"]),
                "",
            ]
        )
    lines.extend(
        [
            "## Recommended Next Round",
            "",
            "- Do not change scorer first: the current failures are primarily recall/pool drift until a case is proven to be scored but ranked below Top-3.",
            "- Do not enter Papers with Code yet: all five expected official repos are concrete GitHub repos; first decide whether direct-fetch identity injection is sufficient for each provider recall miss.",
            "- If a case has direct fetch success but no raw query hit, the narrowest repair is an evidence-backed curated official identity for that specific paper/repo, not a broad retrieval-profile expansion.",
        ]
    )
    return "\n".join(lines) + "\n"


async def main_async(args: argparse.Namespace) -> None:
    benchmark = _index_by_id(_load_json(args.benchmark))
    source_report = _load_json(args.report)
    details = _detail_by_id(source_report)
    cases = []
    for case_id in TARGET_CASE_IDS:
        if case_id not in benchmark:
            raise ValueError(f"benchmark missing target case: {case_id}")
        if case_id not in details:
            raise ValueError(f"benchmark report missing target case detail: {case_id}")
        cases.append(await diagnose_case(benchmark[case_id], details[case_id], top_k=args.top_k))
    classification_counts: dict[str, int] = {}
    for case in cases:
        primary = case["classification"]["primary"]
        classification_counts[primary] = classification_counts.get(primary, 0) + 1
    output = {
        "summary": {
            "target_case_ids": TARGET_CASE_IDS,
            "benchmark_summary": source_report.get("summary") or {},
            "classification_counts": classification_counts,
        },
        "cases": cases,
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    args.markdown_output.write_text(render_markdown(output), encoding="utf-8")
    print(f"Wrote {args.json_output}")
    print(f"Wrote {args.markdown_output}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose live official recall drift cases without changing production logic.")
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MD_OUTPUT)
    parser.add_argument("--top-k", type=int, default=3)
    return parser.parse_args()


def main() -> None:
    asyncio.run(main_async(parse_args()))


if __name__ == "__main__":
    main()
