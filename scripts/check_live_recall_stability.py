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
from app.core.service import PaperReproductionIntelligenceService
from app.providers.github import GitHubProvider
from app.providers.registry import ProviderRegistry
from app.schemas import SearchPaperReposInput


DEFAULT_BENCHMARK = PROJECT_ROOT / "benchmarks" / "paper_repro_benchmark.json"
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "reports" / "live_recall_stability.json"
DEFAULT_MD_OUTPUT = PROJECT_ROOT / "reports" / "live_recall_stability.md"

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


def _repo_key(payload: dict[str, Any]) -> str:
    return _normalize_repo(str(payload.get("full_name") or ""))


def _candidate_aliases(item: Any) -> set[str]:
    aliases = [_normalize_repo(getattr(item, "repo", None))]
    aliases.extend(_normalize_repo(alias) for alias in (getattr(item, "repo_aliases", None) or []))
    metadata = getattr(item, "metadata", None) or {}
    aliases.extend(_normalize_repo(alias) for alias in (metadata.get("repo_aliases") or []))
    return {alias for alias in aliases if alias}


def _rank_of(retrieved_aliases: list[set[str]], expected: set[str]) -> int | None:
    for index, aliases in enumerate(retrieved_aliases, start=1):
        if aliases & expected:
            return index
    return None


def _format_bool(value: bool) -> str:
    return "yes" if value else "no"


def _format_list(values: list[Any], *, empty: str = "none") -> str:
    cleaned = [str(value) for value in values if str(value).strip()]
    return ", ".join(f"`{value}`" for value in cleaned) if cleaned else empty


async def _manual_direct_fetch(provider: GitHubProvider, official_repos: set[str]) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for repo in sorted(official_repos):
        if "/" not in repo:
            results[repo] = {"success": False, "canonical_full_name": None, "error": "repo is not owner/name"}
            continue
        owner, name = repo.split("/", 1)
        payload = await provider._fetch_repository(owner, name)
        results[repo] = {
            "success": payload is not None,
            "canonical_full_name": _repo_key(payload or {}),
            "aliases": list(payload.get("repo_aliases") or []) if payload else [],
            "error": None if payload else provider._repo_errors.get(provider._repo_key(owner, name)) or "not fetched",
            "archived": bool((payload or {}).get("archived")),
            "stars": (payload or {}).get("stargazers_count"),
        }
    return results


async def _collect_provider_pool(
    provider: GitHubProvider,
    analysis: Any,
    official_repos: set[str],
    *,
    top_k: int,
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    sources: dict[str, str] = {}
    raw_search_hits: dict[str, list[dict[str, Any]]] = {repo: [] for repo in official_repos}
    errors: list[str] = []
    candidate_target = min(50, max(top_k * 8, 16))
    per_query = min(20, max(top_k * 3, 10))

    canonical_pairs = [f"{owner}/{repo}".casefold() for owner, repo in provider._canonical_repo_pairs(analysis)]
    direct_payloads = await provider._fetch_canonical_candidates(analysis)
    canonical_direct_names: list[str] = []
    for payload in direct_payloads:
        key = _repo_key(payload)
        if key:
            canonical_direct_names.append(key)
        if key and key not in seen:
            seen.add(key)
            sources[key] = "canonical_direct_fetch"
            items.append(payload)

    query_summaries: list[dict[str, Any]] = []
    stopped_after_query: int | None = None
    queries = provider._build_search_queries(analysis)[:12]
    for query_index, query in enumerate(queries, start=1):
        query_summary = {
            "index": query_index,
            "query": query,
            "included_in_provider_pool": True,
            "official_present": False,
            "official_rank": None,
            "top_repos": [],
            "error": None,
        }
        try:
            repos = await provider._search_repositories(query, per_page=per_query)
        except Exception as exc:
            query_summary["error"] = str(exc)
            errors.append(f"{query}: {exc}")
            query_summaries.append(query_summary)
            continue
        for rank, payload in enumerate(repos, start=1):
            key = _repo_key(payload)
            if rank <= 5:
                query_summary["top_repos"].append(key)
            if key in official_repos:
                query_summary["official_present"] = True
                if query_summary["official_rank"] is None:
                    query_summary["official_rank"] = rank
                raw_search_hits[key].append({"query_index": query_index, "query": query, "rank": rank})
            if key and key not in seen:
                seen.add(key)
                sources[key] = f"search_query_{query_index}"
                items.append(payload)
        query_summaries.append(query_summary)
        if len(items) >= candidate_target:
            stopped_after_query = query_index
            break

    provider_pool_repos = [_repo_key(payload) for payload in items]
    return {
        "candidate_target": candidate_target,
        "per_query": per_query,
        "queries": queries,
        "query_summaries": query_summaries,
        "errors": errors,
        "canonical_pairs": canonical_pairs,
        "canonical_direct_names": canonical_direct_names,
        "provider_pool_repos": provider_pool_repos,
        "provider_pool_sources": sources,
        "official_in_provider_pool": bool(official_repos & set(provider_pool_repos)),
        "official_sources": {
            repo: sources.get(repo)
            for repo in sorted(official_repos)
            if repo in sources
        },
        "official_from_raw_search": any(raw_search_hits.values()),
        "raw_search_hits": raw_search_hits,
        "official_from_canonical_direct_fetch": bool(official_repos & set(canonical_direct_names)),
        "stopped_after_query": stopped_after_query,
    }


async def _run_service_search(provider: GitHubProvider, entry: dict[str, Any], official_repos: set[str], *, top_k: int) -> dict[str, Any]:
    service = PaperReproductionIntelligenceService(registry=ProviderRegistry([provider]))
    output = await service.search_paper_repos(
        SearchPaperReposInput(
            query=entry["query"],
            paper_title=entry.get("paper_title"),
            task=entry.get("task"),
            top_k=top_k,
            include_unofficial=True,
        )
    )
    retrieved_aliases = [_candidate_aliases(item) for item in output.results]
    rank = _rank_of(retrieved_aliases, official_repos)
    return {
        "official_top3": bool(rank and rank <= min(3, top_k)),
        "official_rank": rank,
        "top3_candidates": [_normalize_repo(item.repo) for item in output.results],
        "top3_scores": [item.score for item in output.results],
        "provider_status": output.provider_status,
        "warnings": output.warnings,
    }


def _classify_run(provider_pool: dict[str, Any], service_result: dict[str, Any], direct_fetch: dict[str, Any]) -> str:
    direct_success = any(item.get("success") for item in direct_fetch.values())
    in_pool = bool(provider_pool["official_in_provider_pool"])
    in_top3 = bool(service_result["official_top3"])
    raw_hit = bool(provider_pool["official_from_raw_search"])
    canonical_hit = bool(provider_pool["official_from_canonical_direct_fetch"])
    if in_top3 and not raw_hit and canonical_hit:
        return "raw_search_drift_but_direct_fetch_recovers"
    if in_top3:
        return "stable_top3"
    if not in_pool and direct_success:
        return "intermittent_provider_pool_drop"
    if not in_pool and not direct_success:
        return "persistent_provider_recall_miss"
    if in_pool and not in_top3:
        return "intermittent_top3_drop"
    return "unknown"


async def check_case_run(entry: dict[str, Any], *, run_index: int, top_k: int) -> dict[str, Any]:
    official_repos = {_normalize_repo(repo) for repo in entry.get("official_repos", [])}
    provider = GitHubProvider()
    analysis = analyze_query(
        entry["query"],
        paper_title=entry.get("paper_title"),
        task=entry.get("task"),
        source_types=["github"],
    )
    direct_fetch = await _manual_direct_fetch(provider, official_repos)
    provider_pool = await _collect_provider_pool(provider, analysis, official_repos, top_k=top_k)
    service_result = await _run_service_search(provider, entry, official_repos, top_k=top_k)
    return {
        "run": run_index,
        "case_id": entry["id"],
        "expected_official_repos": sorted(official_repos),
        "official_in_provider_pool": provider_pool["official_in_provider_pool"],
        "official_in_final_top3": service_result["official_top3"],
        "official_rank": service_result["official_rank"],
        "official_from_raw_github_search": provider_pool["official_from_raw_search"],
        "official_from_canonical_direct_fetch": provider_pool["official_from_canonical_direct_fetch"],
        "manual_direct_fetch_succeeded": any(item.get("success") for item in direct_fetch.values()),
        "top3_candidates": service_result["top3_candidates"],
        "top3_scores": service_result["top3_scores"],
        "classification": _classify_run(provider_pool, service_result, direct_fetch),
        "direct_fetch": direct_fetch,
        "provider_pool": {
            "candidate_count": len(provider_pool["provider_pool_repos"]),
            "candidate_target": provider_pool["candidate_target"],
            "stopped_after_query": provider_pool["stopped_after_query"],
            "official_sources": provider_pool["official_sources"],
            "raw_search_hits": provider_pool["raw_search_hits"],
            "canonical_direct_names": provider_pool["canonical_direct_names"],
            "query_summaries": provider_pool["query_summaries"],
            "errors": provider_pool["errors"],
        },
        "provider_status": service_result["provider_status"],
        "warnings": service_result["warnings"],
    }


def _aggregate_case(case_id: str, runs: list[dict[str, Any]], total_runs: int) -> dict[str, Any]:
    ranks = [run["official_rank"] for run in runs if run.get("official_rank")]
    top3_count = sum(1 for run in runs if run["official_in_final_top3"])
    provider_pool_count = sum(1 for run in runs if run["official_in_provider_pool"])
    direct_fetch_count = sum(1 for run in runs if run["manual_direct_fetch_succeeded"])
    raw_search_count = sum(1 for run in runs if run["official_from_raw_github_search"])
    canonical_direct_count = sum(1 for run in runs if run["official_from_canonical_direct_fetch"])
    classification_counts: dict[str, int] = {}
    for run in runs:
        classification = run["classification"]
        classification_counts[classification] = classification_counts.get(classification, 0) + 1
    if top3_count == total_runs:
        aggregate_classification = "stable_top3"
        recommendation = "No production fix recommended now; the full-benchmark miss looks like one-time live drift."
    elif provider_pool_count == 0:
        aggregate_classification = "persistent_provider_recall_miss"
        recommendation = "Consider narrow direct-fetch/identity hardening only after confirming external evidence."
    elif provider_pool_count < total_runs:
        aggregate_classification = "intermittent_provider_pool_drop"
        recommendation = "Consider direct-fetch hardening if drops reproduce; do not change scorer first."
    elif top3_count < total_runs:
        aggregate_classification = "intermittent_top3_drop"
        recommendation = "Run score-focused diagnostics for this case before changing ranking."
    else:
        aggregate_classification = "unknown"
        recommendation = "Repeat targeted diagnostics with provider errors and raw query traces."
    if raw_search_count < total_runs and direct_fetch_count == total_runs and provider_pool_count == total_runs:
        recommendation += " Raw GitHub search is not always enough, but direct/canonical fetch recovered the official repo in this check."
    return {
        "case_id": case_id,
        "runs": total_runs,
        "top3_success_count": top3_count,
        "provider_pool_success_count": provider_pool_count,
        "direct_fetch_success_count": direct_fetch_count,
        "raw_search_seen_count": raw_search_count,
        "canonical_direct_fetch_seen_count": canonical_direct_count,
        "best_rank": min(ranks) if ranks else None,
        "worst_rank": max(ranks) if ranks else None,
        "classification_counts": classification_counts,
        "aggregate_classification": aggregate_classification,
        "recommendation": recommendation,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Live Recall Stability Check",
        "",
        "This report repeats targeted replay for the five current live recall drift cases. It does not modify scorer, retrieval, provider, identity, or benchmark logic.",
        "",
        "## Summary",
        "",
        f"- Runs per case: `{report['summary']['runs']}`",
        f"- Target cases: {_format_list(report['summary']['target_case_ids'])}",
        "",
        "## Aggregate Results",
        "",
        "| Case | Top-3 success | Provider pool | Direct fetch | Raw search | Best rank | Worst rank | Aggregate classification | Recommendation |",
        "|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for aggregate in report["aggregates"]:
        lines.append(
            f"| `{aggregate['case_id']}` | `{aggregate['top3_success_count']}/{aggregate['runs']}` | "
            f"`{aggregate['provider_pool_success_count']}/{aggregate['runs']}` | "
            f"`{aggregate['direct_fetch_success_count']}/{aggregate['runs']}` | "
            f"`{aggregate['raw_search_seen_count']}/{aggregate['runs']}` | "
            f"`{aggregate['best_rank']}` | `{aggregate['worst_rank']}` | "
            f"`{aggregate['aggregate_classification']}` | {aggregate['recommendation']} |"
        )
    lines.extend(["", "## Per-Run Results", ""])
    for case in report["cases"]:
        lines.extend(
            [
                f"### `{case['case_id']}`",
                "",
                "| Run | Top-3 | Rank | Provider pool | Raw search | Canonical direct | Direct fetch | Top-3 candidates | Classification |",
                "|---:|---|---:|---|---|---|---|---|---|",
            ]
        )
        for run in case["runs"]:
            lines.append(
                f"| {run['run']} | {_format_bool(run['official_in_final_top3'])} | "
                f"`{run['official_rank']}` | {_format_bool(run['official_in_provider_pool'])} | "
                f"{_format_bool(run['official_from_raw_github_search'])} | "
                f"{_format_bool(run['official_from_canonical_direct_fetch'])} | "
                f"{_format_bool(run['manual_direct_fetch_succeeded'])} | "
                f"{_format_list(run['top3_candidates'])} | `{run['classification']}` |"
            )
        lines.append("")
    lines.extend(
        [
            "## Recommendation",
            "",
            "- If a case is `5/5` Top-3 here, treat the full-benchmark miss as live GitHub drift rather than a production-logic failure.",
            "- If future runs show provider-pool drops while direct fetch keeps succeeding, prefer a narrow canonical seed/direct-fetch hardening pass over Papers with Code.",
            "- Only analyze scorer/ranking for a case that repeatedly has the official repo in provider pool but drops from final Top-3.",
        ]
    )
    return "\n".join(lines) + "\n"


async def main_async(args: argparse.Namespace) -> None:
    benchmark = _index_by_id(_load_json(args.benchmark))
    case_runs: dict[str, list[dict[str, Any]]] = {case_id: [] for case_id in TARGET_CASE_IDS}
    for run_index in range(1, args.runs + 1):
        print(f"Starting stability run {run_index}/{args.runs}")
        for case_id in TARGET_CASE_IDS:
            if case_id not in benchmark:
                raise ValueError(f"benchmark missing target case: {case_id}")
            result = await check_case_run(benchmark[case_id], run_index=run_index, top_k=args.top_k)
            case_runs[case_id].append(result)
            print(
                f"  {case_id}: top3={result['official_in_final_top3']} "
                f"rank={result['official_rank']} class={result['classification']}"
            )
    aggregates = [_aggregate_case(case_id, runs, args.runs) for case_id, runs in case_runs.items()]
    report = {
        "summary": {
            "runs": args.runs,
            "top_k": args.top_k,
            "target_case_ids": TARGET_CASE_IDS,
        },
        "aggregates": aggregates,
        "cases": [
            {
                "case_id": case_id,
                "runs": runs,
            }
            for case_id, runs in case_runs.items()
        ],
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    args.markdown_output.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote {args.json_output}")
    print(f"Wrote {args.markdown_output}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Repeat targeted live recall replay for five drift cases.")
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MD_OUTPUT)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--top-k", type=int, default=3)
    return parser.parse_args()


def main() -> None:
    asyncio.run(main_async(parse_args()))


if __name__ == "__main__":
    main()
