from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.tools.paper_tools import compare_paper_repos_tool, inspect_paper_repo_tool, search_paper_repos_tool

try:
    from scripts.evaluate_benchmark import DEFAULT_BENCHMARK, load_benchmark
except ModuleNotFoundError:
    from evaluate_benchmark import DEFAULT_BENCHMARK, load_benchmark


DEFAULT_CASE_IDS = ["sam_2023", "detr_2020", "nerf_2020", "dreambooth_2022", "alphafold_2021"]
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "reports" / "case_studies.md"


def _normalize_repo(repo: str | None) -> str:
    return (repo or "").strip().lower()


def _select_cases(entries: list[dict[str, Any]], case_ids: list[str], limit: int | None) -> list[dict[str, Any]]:
    by_id = {entry["id"]: entry for entry in entries}
    selected = [by_id[case_id] for case_id in case_ids if case_id in by_id]
    return selected[:limit] if limit else selected


def _provider_errors(provider_status: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for provider, status in provider_status.items():
        if isinstance(status, dict) and not status.get("ok", True):
            errors.append(f"{provider}: {status.get('error') or 'provider failed'}")
    return errors


def _candidate_repos(search_results: list[Any], entry: dict[str, Any]) -> list[str]:
    repos = [_normalize_repo(item.repo) for item in search_results if item.repo]
    labeled = [
        *entry.get("official_repos", []),
        *entry.get("high_quality_reproduction_repos", []),
        *entry.get("common_distractor_repos", [])[:1],
    ]
    for repo in labeled:
        normalized = _normalize_repo(repo)
        if normalized and normalized not in repos:
            repos.append(normalized)
    return repos[:4]


def _format_judgement(value: Any) -> str:
    if isinstance(value, dict):
        level = value.get("level") or "unknown"
        reason = value.get("reason") or ""
        evidence = value.get("evidence") or []
        evidence_text = f" evidence={evidence[:3]}" if evidence else ""
        return f"{level}: {reason}{evidence_text}".strip()
    return str(value or "unknown")


def _format_repo_list(repos: list[str] | None) -> str:
    values = [f"`{repo}`" for repo in (repos or [])]
    return ", ".join(values) if values else "None"


async def run_case(entry: dict[str, Any], *, top_k: int) -> dict[str, Any]:
    case: dict[str, Any] = {
        "id": entry["id"],
        "paper_title": entry["paper_title"],
        "query": entry["query"],
        "task": entry.get("task"),
    }
    search = await search_paper_repos_tool(
        query=entry["query"],
        paper_title=entry.get("paper_title"),
        task=entry.get("task"),
        top_k=top_k,
    )
    provider_errors = _provider_errors(search.provider_status)
    case["provider_errors"] = provider_errors
    case["top_candidates"] = [
        {
            "repo": item.repo,
            "role": item.repo_role,
            "score": item.score,
            "cap_reason": item.cap_reason,
            "evidence": item.positive_evidence[:3],
        }
        for item in search.results
    ]
    repos = _candidate_repos(search.results, entry)
    if repos:
        inspected = await inspect_paper_repo_tool(
            repo=repos[0],
            query=entry["query"],
            include_readme=True,
            include_tree=True,
        )
        case["inspection"] = {
            "repo": inspected.repo,
            "error": inspected.error,
            "role": inspected.repo_role,
            "score": inspected.score,
            "training_readiness": inspected.training_readiness or inspected.inspection_signals.get("training_readiness"),
            "evaluation_readiness": inspected.evaluation_readiness or inspected.inspection_signals.get("evaluation_readiness"),
            "environment_reproducibility": inspected.environment_reproducibility
            or inspected.inspection_signals.get("environment_reproducibility"),
            "paper_identity_confidence": inspected.paper_identity_confidence
            or inspected.inspection_signals.get("paper_identity_confidence"),
            "training_entries": inspected.inspection_signals.get("training_entries", [])[:4],
            "evaluation_entries": inspected.inspection_signals.get("evaluation_entries", [])[:4],
            "checkpoint_links": inspected.inspection_signals.get("checkpoint_links", [])[:3],
            "negative_evidence": inspected.negative_evidence[:3],
        }
    if len(repos) >= 2:
        compared = await compare_paper_repos_tool(
            repos=repos[:4],
            query=entry["query"],
            criteria=["direct reproduction", "method reference", "baseline", "risk"],
            include_details=True,
        )
        case["compare"] = {
            "best_overall": compared.best_overall,
            "best_for_direct_reproduction": compared.best_for_direct_reproduction,
            "best_for_method_reference": compared.best_for_method_reference,
            "best_for_baseline": compared.best_for_baseline,
            "not_recommended": compared.not_recommended,
            "recommendation_summary": getattr(compared, "recommendation_summary", ""),
            "recommendation": compared.recommendation,
            "failed_repos": [item.model_dump() for item in compared.failed_repos],
        }
    return case


async def run_cases(entries: list[dict[str, Any]], *, top_k: int, sleep_seconds: float) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for entry in entries:
        try:
            cases.append(await run_case(entry, top_k=top_k))
        except Exception as exc:
            cases.append({"id": entry.get("id"), "paper_title": entry.get("paper_title"), "query": entry.get("query"), "error": str(exc)})
        if sleep_seconds > 0:
            await asyncio.sleep(sleep_seconds)
    return cases


def render_skipped(cases: list[dict[str, Any]], reason: str) -> str:
    lines = [
        "# Paper Reproduction Case Studies",
        "",
        f"Live workflow was skipped: {reason}",
        "",
    ]
    for entry in cases:
        lines.extend(
            [
                f"## {entry['paper_title']}",
                "",
                f"- Case ID: `{entry['id']}`",
                f"- Query: `{entry['query']}`",
                f"- Task: `{entry.get('task') or 'unknown'}`",
                f"- Labeled official repos: {_format_repo_list(entry.get('official_repos'))}",
                f"- Labeled high-quality reproductions: {_format_repo_list(entry.get('high_quality_reproduction_repos'))}",
                f"- Labeled distractors: {_format_repo_list(entry.get('common_distractor_repos'))}",
                "- Top candidates: unavailable until live search runs.",
                "- Deep inspection: unavailable until live inspect runs.",
                "- Compare recommendation: unavailable until live compare runs.",
                "",
            ]
        )
    lines.extend(
        [
            "Run with a GitHub token:",
            "",
            "```powershell",
            ".\\.venv\\Scripts\\python.exe scripts\\generate_case_studies.py",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def render_case_studies(cases: list[dict[str, Any]]) -> str:
    lines = ["# Paper Reproduction Case Studies", ""]
    for case in cases:
        lines.extend(
            [
                f"## {case.get('paper_title')}",
                "",
                f"- Case ID: `{case.get('id')}`",
                f"- Query: `{case.get('query')}`",
            ]
        )
        if case.get("error"):
            lines.extend(["", f"Workflow error: {case['error']}", ""])
            continue
        if case.get("provider_errors"):
            lines.append(f"- Provider errors: {'; '.join(case['provider_errors'])}")
        lines.extend(["", "### Top Candidates", ""])
        candidates = case.get("top_candidates") or []
        if not candidates:
            lines.append("- No candidates returned.")
        else:
            for item in candidates:
                evidence = "; ".join(item.get("evidence") or [])
                lines.append(
                    f"- `{item.get('repo')}` role=`{item.get('role')}` score=`{item.get('score')}` "
                    f"cap=`{item.get('cap_reason')}` evidence={evidence}"
                )
        inspection = case.get("inspection") or {}
        lines.extend(["", "### Deep Inspection", ""])
        if not inspection:
            lines.append("- No repository was inspected.")
        elif inspection.get("error"):
            lines.append(f"- `{inspection.get('repo')}` inspection failed: {inspection.get('error')}")
        else:
            lines.extend(
                [
                    f"- Inspected repo: `{inspection.get('repo')}` role=`{inspection.get('role')}` score=`{inspection.get('score')}`",
                    f"- Training readiness: {_format_judgement(inspection.get('training_readiness'))} entries={inspection.get('training_entries')}",
                    f"- Evaluation readiness: {_format_judgement(inspection.get('evaluation_readiness'))} entries={inspection.get('evaluation_entries')}",
                    f"- Environment reproducibility: {_format_judgement(inspection.get('environment_reproducibility'))}",
                    f"- Paper identity confidence: {_format_judgement(inspection.get('paper_identity_confidence'))}",
                    f"- Checkpoint links: {inspection.get('checkpoint_links')}",
                ]
            )
        compare = case.get("compare") or {}
        lines.extend(["", "### Compare Decision", ""])
        if not compare:
            lines.append("- Not enough candidates to compare.")
        else:
            lines.extend(
                [
                    f"- Best overall: `{compare.get('best_overall')}`",
                    f"- Direct reproduction: `{compare.get('best_for_direct_reproduction')}`",
                    f"- Method reference: `{compare.get('best_for_method_reference')}`",
                    f"- Baseline: `{compare.get('best_for_baseline')}`",
                    f"- Not recommended: {compare.get('not_recommended')}",
                    f"- Summary: {compare.get('recommendation_summary') or compare.get('recommendation')}",
                ]
            )
        lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate end-to-end paper reproduction case studies.")
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--case-id", action="append", dest="case_ids", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--allow-unauthenticated", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    entries = load_benchmark(args.benchmark)
    selected = _select_cases(entries, args.case_ids or DEFAULT_CASE_IDS, args.limit)
    settings = get_settings()
    if not settings.github_token and not args.allow_unauthenticated:
        rendered = render_skipped(
            selected,
            "GITHUB_TOKEN is not configured. Use --allow-unauthenticated for a small risky smoke run, or set GITHUB_TOKEN in .env.",
        )
    else:
        cases = asyncio.run(run_cases(selected, top_k=args.top_k, sleep_seconds=max(0.0, args.sleep_seconds)))
        rendered = render_case_studies(cases)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
