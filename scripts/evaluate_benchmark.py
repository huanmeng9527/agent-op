from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.tools.paper_tools import search_paper_repos_tool


DEFAULT_BENCHMARK = Path(__file__).resolve().parents[1] / "benchmarks" / "paper_repro_benchmark.json"
DEFAULT_JSON_REPORT = Path(__file__).resolve().parents[1] / "reports" / "benchmark_report.json"
DEFAULT_MARKDOWN_REPORT = Path(__file__).resolve().parents[1] / "reports" / "benchmark_report.md"


@dataclass
class BenchmarkStats:
    total: int = 0
    attempted: int = 0
    evaluated: int = 0
    top1_hit: int = 0
    top3_hit: int = 0
    official_top1_hit: int = 0
    official_top3_hit: int = 0
    distractor_top1: int = 0
    failed: int = 0
    provider_failed: int = 0
    rate_limited: int = 0
    stopped_early: bool = False
    stop_reason: str | None = None


def _normalize_repo(repo: str | None) -> str:
    return (repo or "").strip().lower()


def load_benchmark(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        entries = json.load(file)
    if not isinstance(entries, list):
        raise ValueError("benchmark must be a JSON list")
    for index, entry in enumerate(entries):
        for key in ("id", "paper_title", "query", "official_repos", "high_quality_reproduction_repos", "common_distractor_repos"):
            if key not in entry:
                raise ValueError(f"entry {index} missing required key: {key}")
    return entries


def _hit(retrieved: list[str], expected: set[str], k: int) -> bool:
    return any(repo in expected for repo in retrieved[:k])


def _provider_errors(provider_status: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for provider, status in provider_status.items():
        if isinstance(status, dict) and not status.get("ok", True):
            errors.append(f"{provider}: {status.get('error') or 'provider failed'}")
    return errors


def _is_rate_limit_error(errors: list[str]) -> bool:
    joined = " ".join(errors).casefold()
    return "rate limit" in joined or "http 403" in joined


def _rank_of(retrieved: list[str], expected: set[str]) -> int | None:
    for index, repo in enumerate(retrieved, start=1):
        if repo in expected:
            return index
    return None


def classify_retrieval_cause(
    *,
    retrieved: list[str],
    official_rank: int | None,
    acceptable_rank: int | None,
    distractor_rank: int | None,
    has_official: bool,
    provider_failed: bool = False,
    rate_limited: bool = False,
    error: str | None = None,
) -> str:
    if error:
        return "code_exception"
    if rate_limited:
        return "github_rate_limit"
    if provider_failed:
        return "provider_error"
    if not retrieved:
        return "no_results"
    if distractor_rank == 1:
        return "distractor_ranked_1"
    if acceptable_rank is None:
        return "official_repo_not_recalled" if has_official and official_rank is None else "expected_repo_not_recalled"
    if acceptable_rank > 3:
        return "expected_repo_ranked_below_top3"
    if has_official and official_rank and official_rank > 1:
        return "official_recalled_not_top1"
    if acceptable_rank > 1:
        return "expected_recalled_not_top1"
    return "success"


async def evaluate_entry(entry: dict[str, Any], *, top_k: int) -> dict[str, Any]:
    result = await search_paper_repos_tool(
        query=entry["query"],
        paper_title=entry.get("paper_title"),
        task=entry.get("task"),
        top_k=top_k,
        include_unofficial=True,
    )
    retrieved = [_normalize_repo(item.repo) for item in result.results]
    official = {_normalize_repo(repo) for repo in entry.get("official_repos", [])}
    reproductions = {_normalize_repo(repo) for repo in entry.get("high_quality_reproduction_repos", [])}
    distractors = {_normalize_repo(repo) for repo in entry.get("common_distractor_repos", [])}
    acceptable = official | reproductions
    provider_errors = _provider_errors(result.provider_status)
    official_rank = _rank_of(retrieved, official)
    acceptable_rank = _rank_of(retrieved, acceptable)
    distractor_rank = _rank_of(retrieved, distractors)
    provider_failed = bool(provider_errors)
    rate_limited = _is_rate_limit_error(provider_errors)
    return {
        "id": entry["id"],
        "paper_title": entry["paper_title"],
        "task": entry.get("task") or "unknown",
        "retrieved": retrieved,
        "top1_hit": _hit(retrieved, acceptable, 1),
        "top3_hit": _hit(retrieved, acceptable, min(3, top_k)),
        "official_top1_hit": _hit(retrieved, official, 1) if official else False,
        "official_top3_hit": _hit(retrieved, official, min(3, top_k)) if official else False,
        "distractor_top1": bool(retrieved and retrieved[0] in distractors),
        "official_rank": official_rank,
        "acceptable_rank": acceptable_rank,
        "distractor_rank": distractor_rank,
        "official_repos": sorted(official),
        "high_quality_reproduction_repos": sorted(reproductions),
        "common_distractor_repos": sorted(distractors),
        "warnings": result.warnings,
        "provider_status": result.provider_status,
        "provider_errors": provider_errors,
        "provider_failed": provider_failed,
        "rate_limited": rate_limited,
        "failure_cause": classify_retrieval_cause(
            retrieved=retrieved,
            official_rank=official_rank,
            acceptable_rank=acceptable_rank,
            distractor_rank=distractor_rank,
            has_official=bool(official),
            provider_failed=provider_failed,
            rate_limited=rate_limited,
        ),
    }


async def evaluate(
    entries: list[dict[str, Any]],
    *,
    top_k: int,
    sleep_seconds: float = 0.0,
) -> tuple[BenchmarkStats, list[dict[str, Any]]]:
    stats = BenchmarkStats(total=len(entries))
    details: list[dict[str, Any]] = []
    for entry in entries:
        stats.attempted += 1
        try:
            detail = await evaluate_entry(entry, top_k=top_k)
        except Exception as exc:
            stats.failed += 1
            detail = {
                "id": entry.get("id"),
                "paper_title": entry.get("paper_title"),
                "task": entry.get("task") or "unknown",
                "error": str(exc),
                "failure_cause": "code_exception",
            }
        details.append(detail)
        if detail.get("provider_failed"):
            stats.provider_failed += 1
            stats.rate_limited += int(bool(detail.get("rate_limited")))
            if detail.get("rate_limited"):
                stats.stopped_early = True
                stats.stop_reason = "github_rate_limit"
                break
            if sleep_seconds > 0:
                await asyncio.sleep(sleep_seconds)
            continue
        if detail.get("error"):
            if sleep_seconds > 0:
                await asyncio.sleep(sleep_seconds)
            continue
        stats.evaluated += 1
        stats.top1_hit += int(bool(detail.get("top1_hit")))
        stats.top3_hit += int(bool(detail.get("top3_hit")))
        stats.official_top1_hit += int(bool(detail.get("official_top1_hit")))
        stats.official_top3_hit += int(bool(detail.get("official_top3_hit")))
        stats.distractor_top1 += int(bool(detail.get("distractor_top1")))
        if sleep_seconds > 0:
            await asyncio.sleep(sleep_seconds)
    return stats, details


def _rate(value: int, total: int) -> float:
    return round(value / total, 4) if total else 0.0


def build_report(stats: BenchmarkStats, details: list[dict[str, Any]]) -> dict[str, Any]:
    by_task: dict[str, dict[str, Any]] = {}
    failure_summary_by_task: dict[str, dict[str, Any]] = {}
    failure_summary_by_cause: dict[str, dict[str, Any]] = {}
    for detail in details:
        cause = detail.get("failure_cause") or "unknown"
        is_failure = cause != "success"
        if is_failure:
            task = detail.get("task") or "unknown"
            task_bucket = failure_summary_by_task.setdefault(task, {"count": 0, "examples": []})
            task_bucket["count"] += 1
            task_bucket["examples"].append(detail.get("id") or detail.get("paper_title"))
            cause_bucket = failure_summary_by_cause.setdefault(cause, {"count": 0, "examples": []})
            cause_bucket["count"] += 1
            cause_bucket["examples"].append(detail.get("id") or detail.get("paper_title"))
        if detail.get("error") or detail.get("provider_failed"):
            continue
        task = detail.get("task") or "unknown"
        bucket = by_task.setdefault(task, {"total": 0, "top1_hit": 0, "top3_hit": 0, "distractor_top1": 0})
        bucket["total"] += 1
        bucket["top1_hit"] += int(bool(detail.get("top1_hit")))
        bucket["top3_hit"] += int(bool(detail.get("top3_hit")))
        bucket["distractor_top1"] += int(bool(detail.get("distractor_top1")))
    task_summary = {
        task: {
            **values,
            "top1_hit_rate": _rate(values["top1_hit"], values["total"]),
            "top3_hit_rate": _rate(values["top3_hit"], values["total"]),
            "distractor_top1_rate": _rate(values["distractor_top1"], values["total"]),
        }
        for task, values in sorted(by_task.items())
    }
    return {
        "summary": {
            "total": stats.total,
            "attempted": stats.attempted,
            "evaluated": stats.evaluated,
            "unprocessed": max(0, stats.total - stats.attempted),
            "failed": stats.failed,
            "provider_failed": stats.provider_failed,
            "rate_limited": stats.rate_limited,
            "stopped_early": stats.stopped_early,
            "stop_reason": stats.stop_reason,
            "top1_hit_rate": _rate(stats.top1_hit, stats.evaluated),
            "top3_hit_rate": _rate(stats.top3_hit, stats.evaluated),
            "official_top1_hit_rate": _rate(stats.official_top1_hit, stats.evaluated),
            "official_top3_hit_rate": _rate(stats.official_top3_hit, stats.evaluated),
            "distractor_top1_rate": _rate(stats.distractor_top1, stats.evaluated),
        },
        "by_task": task_summary,
        "failure_summary_by_task": {
            task: {**values, "examples": values["examples"][:5]}
            for task, values in sorted(failure_summary_by_task.items())
        },
        "failure_summary_by_cause": {
            cause: {**values, "examples": values["examples"][:8]}
            for cause, values in sorted(failure_summary_by_cause.items())
        },
        "failure_examples": [
            detail
            for detail in details
            if (detail.get("failure_cause") or "success") != "success"
        ][:12],
        "details": details,
    }


def build_skipped_report(entries: list[dict[str, Any]], *, reason: str) -> dict[str, Any]:
    return {
        "summary": {
            "total": len(entries),
            "attempted": 0,
            "evaluated": 0,
            "unprocessed": len(entries),
            "failed": 0,
            "provider_failed": 0,
            "rate_limited": 0,
            "status": "skipped",
            "issue_class": "configuration",
            "reason": reason,
        },
        "by_task": {},
        "failure_summary_by_task": {},
        "failure_summary_by_cause": {
            "configuration_missing_token": {
                "count": len(entries),
                "examples": [entry.get("id") for entry in entries[:8]],
            }
        },
        "failure_examples": [],
        "details": [],
    }


def render_markdown_report(report: dict[str, Any], *, benchmark_path: Path, top_k: int) -> str:
    summary = report.get("summary", {})
    try:
        display_path = benchmark_path.resolve().relative_to(Path.cwd().resolve())
    except ValueError:
        display_path = benchmark_path
    lines = [
        "# Paper Reproduction Benchmark Report",
        "",
        f"- Benchmark file: `{display_path}`",
        f"- Top-k: `{top_k}`",
        f"- Total cases: `{summary.get('total', 0)}`",
        f"- Attempted live cases: `{summary.get('attempted', 0)}`",
        f"- Evaluated cases: `{summary.get('evaluated', 0)}`",
        f"- Unprocessed cases: `{summary.get('unprocessed', 0)}`",
        f"- Failed cases: `{summary.get('failed', 0)}`",
        f"- Provider failed cases: `{summary.get('provider_failed', 0)}`",
        f"- Rate limited cases: `{summary.get('rate_limited', 0)}`",
        "",
    ]
    if summary.get("status") == "skipped":
        lines.extend(
            [
                "## Status",
                "",
                f"Live benchmark was skipped: {summary.get('reason')}",
                f"Issue class: `{summary.get('issue_class', 'configuration')}`",
                "",
                "## Failure Summary By Cause",
                "",
            ]
        )
        failure_summary_by_cause = report.get("failure_summary_by_cause") or {}
        if not failure_summary_by_cause:
            lines.append("- No failure cause was recorded.")
        else:
            for cause, values in failure_summary_by_cause.items():
                examples = ", ".join(f"`{item}`" for item in values.get("examples") or [])
                lines.append(f"- `{cause}`: {values.get('count', 0)} cases; examples: {examples}")
        lines.extend(
            [
                "",
                "Set `GITHUB_TOKEN` in `.env`, then run:",
                "",
                "```powershell",
                ".\\.venv\\Scripts\\python.exe scripts\\evaluate_benchmark.py --top-k 3",
                "```",
                "",
            ]
        )
        return "\n".join(lines)

    lines.extend(
        [
            "## Summary",
            "",
            f"- Top-1 hit rate: `{summary.get('top1_hit_rate', 0)}`",
            f"- Top-3 hit rate: `{summary.get('top3_hit_rate', 0)}`",
            f"- Official repo top-1 hit rate: `{summary.get('official_top1_hit_rate', 0)}`",
            f"- Official repo top-3 hit rate: `{summary.get('official_top3_hit_rate', 0)}`",
            f"- Distractor ranked #1 rate: `{summary.get('distractor_top1_rate', 0)}`",
            f"- Stopped early: `{summary.get('stopped_early', False)}`",
            f"- Stop reason: `{summary.get('stop_reason') or 'none'}`",
            "",
            "## By Task",
            "",
            "| Task | Cases | Top-1 | Top-3 | Distractor #1 |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for task, values in (report.get("by_task") or {}).items():
        lines.append(
            f"| {task} | {values.get('total', 0)} | {values.get('top1_hit_rate', 0)} | "
            f"{values.get('top3_hit_rate', 0)} | {values.get('distractor_top1_rate', 0)} |"
        )
    failures = report.get("failure_examples") or []
    failure_summary_by_cause = report.get("failure_summary_by_cause") or {}
    lines.extend(["", "## Failure Summary By Cause", ""])
    if not failure_summary_by_cause:
        lines.append("- No failures or non-ideal rankings grouped by cause.")
    else:
        for cause, values in failure_summary_by_cause.items():
            examples = ", ".join(f"`{item}`" for item in values.get("examples") or [])
            lines.append(f"- `{cause}`: {values.get('count', 0)} cases; examples: {examples}")
    failure_summary_by_task = report.get("failure_summary_by_task") or {}
    lines.extend(["", "## Failure Summary By Task", ""])
    if not failure_summary_by_task:
        lines.append("- No provider failures or top-3 misses grouped by task.")
    else:
        for task, values in failure_summary_by_task.items():
            examples = ", ".join(f"`{item}`" for item in values.get("examples") or [])
            lines.append(f"- `{task}`: {values.get('count', 0)} cases; examples: {examples}")
    lines.extend(["", "## Failure Examples", ""])
    if not failures:
        lines.append("- No failures or top-3 misses in this run.")
    else:
        for detail in failures:
            if detail.get("provider_failed"):
                reason = "; ".join(detail.get("provider_errors") or ["provider failed"])
            else:
                reason = detail.get("error") or detail.get("failure_cause") or "top-3 miss"
            retrieved = ", ".join(detail.get("retrieved") or [])
            lines.append(f"- `{detail.get('id')}` {detail.get('paper_title')}: {reason}; retrieved: {retrieved}")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate paper reproduction retrieval quality.")
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--output", type=Path, default=DEFAULT_JSON_REPORT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_REPORT)
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    parser.add_argument("--allow-unauthenticated", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    entries = load_benchmark(args.benchmark)
    if args.limit:
        entries = entries[: args.limit]
    if args.validate_only:
        print(json.dumps({"entries": len(entries), "status": "ok"}, ensure_ascii=False, indent=2))
        return
    settings = get_settings()
    if not settings.github_token and not args.allow_unauthenticated:
        report = build_skipped_report(
            entries,
            reason="GITHUB_TOKEN is not configured. Use --allow-unauthenticated for a small risky run, or set GITHUB_TOKEN in .env.",
        )
    else:
        stats, details = asyncio.run(evaluate(entries, top_k=args.top_k, sleep_seconds=max(0.0, args.sleep_seconds)))
        report = build_report(stats, details)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(
            render_markdown_report(report, benchmark_path=args.benchmark, top_k=args.top_k),
            encoding="utf-8",
        )
    print(rendered)


if __name__ == "__main__":
    main()
