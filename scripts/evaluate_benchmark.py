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
DEFAULT_TARGETED_JSON_REPORT = Path(__file__).resolve().parents[1] / "reports" / "targeted_benchmark_report.json"
DEFAULT_TARGETED_MARKDOWN_REPORT = Path(__file__).resolve().parents[1] / "reports" / "targeted_benchmark_report.md"
DEFAULT_IDENTITY_OVERRIDES = Path(__file__).resolve().parents[1] / "data" / "paper_code_identity_overrides.json"


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


def _unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        normalized = value.strip()
        key = normalized.casefold()
        if not normalized or key in seen:
            continue
        seen.add(key)
        output.append(normalized)
    return output


def _split_case_ids(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def load_case_ids_file(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    case_ids = []
    for line in lines:
        clean = line.split("#", 1)[0].strip()
        if clean:
            case_ids.extend(_split_case_ids(clean))
    return case_ids


def load_identity_override_case_ids(path: Path = DEFAULT_IDENTITY_OVERRIDES) -> list[str]:
    if not path.exists():
        raise ValueError(f"identity overrides file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("identity overrides must be a JSON list")
    return [
        str(entry.get("paper_id")).strip()
        for entry in payload
        if isinstance(entry, dict) and str(entry.get("paper_id") or "").strip()
    ]


def selected_case_ids_from_args(args: argparse.Namespace) -> list[str]:
    case_ids: list[str] = []
    for case_id in args.case_id or []:
        case_ids.extend(_split_case_ids(case_id))
    case_ids.extend(_split_case_ids(args.case_ids))
    if args.case_ids_file:
        case_ids.extend(load_case_ids_file(args.case_ids_file))
    if args.identity_overrides:
        case_ids.extend(load_identity_override_case_ids(DEFAULT_IDENTITY_OVERRIDES))
    return _unique_preserve_order(case_ids)


def select_benchmark_entries(entries: list[dict[str, Any]], case_ids: list[str]) -> list[dict[str, Any]]:
    if not case_ids:
        return entries
    by_id = {str(entry.get("id")): entry for entry in entries}
    missing = [case_id for case_id in case_ids if case_id not in by_id]
    if missing:
        raise ValueError(f"case id(s) not found in benchmark: {', '.join(missing)}")
    return [by_id[case_id] for case_id in case_ids]


def resolve_report_paths(args: argparse.Namespace, *, targeted: bool) -> tuple[Path | None, Path | None]:
    if args.report_prefix:
        reports_dir = Path(__file__).resolve().parents[1] / "reports"
        return (
            args.output or reports_dir / f"{args.report_prefix}_benchmark_report.json",
            args.markdown_output or reports_dir / f"{args.report_prefix}_benchmark_report.md",
        )
    if targeted:
        return (
            args.output or DEFAULT_TARGETED_JSON_REPORT,
            args.markdown_output or DEFAULT_TARGETED_MARKDOWN_REPORT,
        )
    return (
        args.output or DEFAULT_JSON_REPORT,
        args.markdown_output or DEFAULT_MARKDOWN_REPORT,
    )


def annotate_targeted_report(report: dict[str, Any], case_ids: list[str]) -> dict[str, Any]:
    if not case_ids:
        return report
    summary = report.setdefault("summary", {})
    summary["selected_case_count"] = len(case_ids)
    summary["selected_case_ids"] = case_ids
    return report


def _candidate_aliases(item: Any) -> set[str]:
    aliases = [_normalize_repo(getattr(item, "repo", None))]
    aliases.extend(_normalize_repo(alias) for alias in (getattr(item, "repo_aliases", None) or []))
    metadata = getattr(item, "metadata", None) or {}
    aliases.extend(_normalize_repo(alias) for alias in (metadata.get("repo_aliases") or []))
    return {alias for alias in aliases if alias}


def _candidate_identity(item: Any) -> dict[str, Any]:
    metadata = getattr(item, "metadata", None) or {}
    external_identity = metadata.get("external_identity") if isinstance(metadata.get("external_identity"), dict) else {}
    return {
        "source": getattr(item, "identity_source", None) or external_identity.get("source"),
        "confidence": getattr(item, "identity_confidence", None) or external_identity.get("confidence"),
        "identity_type": getattr(item, "identity_type", None) or external_identity.get("identity_type"),
        "evidence": list(getattr(item, "identity_evidence", None) or []),
    }


def _hit(retrieved_aliases: list[set[str]], expected: set[str], k: int) -> bool:
    return any(aliases & expected for aliases in retrieved_aliases[:k])


def _provider_errors(provider_status: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for provider, status in provider_status.items():
        if isinstance(status, dict) and not status.get("ok", True):
            errors.append(f"{provider}: {status.get('error') or 'provider failed'}")
    return errors


def _is_rate_limit_error(errors: list[str]) -> bool:
    joined = " ".join(errors).casefold()
    return "rate limit" in joined or "http 403" in joined


def _rank_of(retrieved_aliases: list[set[str]], expected: set[str]) -> int | None:
    for index, aliases in enumerate(retrieved_aliases, start=1):
        if aliases & expected:
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
    retrieved_aliases = [_candidate_aliases(item) for item in result.results]
    official = {_normalize_repo(repo) for repo in entry.get("official_repos", [])}
    reproductions = {_normalize_repo(repo) for repo in entry.get("high_quality_reproduction_repos", [])}
    distractors = {_normalize_repo(repo) for repo in entry.get("common_distractor_repos", [])}
    acceptable = official | reproductions
    provider_errors = _provider_errors(result.provider_status)
    official_rank = _rank_of(retrieved_aliases, official)
    acceptable_rank = _rank_of(retrieved_aliases, acceptable)
    distractor_rank = _rank_of(retrieved_aliases, distractors)
    provider_failed = bool(provider_errors)
    rate_limited = _is_rate_limit_error(provider_errors)
    return {
        "id": entry["id"],
        "paper_title": entry["paper_title"],
        "task": entry.get("task") or "unknown",
        "retrieved": retrieved,
        "retrieved_repo_aliases": [sorted(aliases) for aliases in retrieved_aliases],
        "retrieved_identity": [_candidate_identity(item) for item in result.results],
        "top1_hit": _hit(retrieved_aliases, acceptable, 1),
        "top3_hit": _hit(retrieved_aliases, acceptable, min(3, top_k)),
        "official_top1_hit": _hit(retrieved_aliases, official, 1) if official else False,
        "official_top3_hit": _hit(retrieved_aliases, official, min(3, top_k)) if official else False,
        "distractor_top1": bool(retrieved_aliases and retrieved_aliases[0] & distractors),
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
    is_targeted = "selected_case_count" in summary
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
        *([f"- Selected cases: `{summary.get('selected_case_count', 0)}`"] if is_targeted else []),
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
    if is_targeted and report.get("details"):
        lines.extend(
            [
                "",
                "## Per-Case Results",
                "",
                "| Case | Top-1 | Top-3 | Official Top-1 | Official Top-3 | Distractor #1 | Cause | Retrieved |",
                "|---|---:|---:|---:|---:|---:|---|---|",
            ]
        )
        for detail in report.get("details") or []:
            retrieved = ", ".join(f"`{repo}`" for repo in detail.get("retrieved") or [])
            lines.append(
                f"| `{detail.get('id')}` | `{bool(detail.get('top1_hit'))}` | `{bool(detail.get('top3_hit'))}` | "
                f"`{bool(detail.get('official_top1_hit'))}` | `{bool(detail.get('official_top3_hit'))}` | "
                f"`{bool(detail.get('distractor_top1'))}` | `{detail.get('failure_cause') or 'unknown'}` | {retrieved} |"
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
    parser.add_argument("--case-id", action="append", default=[], help="Run one benchmark case id. Can be repeated.")
    parser.add_argument("--case-ids", default=None, help="Comma-separated benchmark case ids to run.")
    parser.add_argument("--case-ids-file", type=Path, default=None, help="File with case ids, one per line or comma-separated.")
    parser.add_argument("--identity-overrides", action="store_true", help="Run paper ids listed in data/paper_code_identity_overrides.json.")
    parser.add_argument("--report-prefix", default=None, help="Write reports/<prefix>_benchmark_report.json and .md unless explicit outputs are set.")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--markdown-output", type=Path, default=None)
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    parser.add_argument("--allow-unauthenticated", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    entries = load_benchmark(args.benchmark)
    case_ids = selected_case_ids_from_args(args)
    try:
        entries = select_benchmark_entries(entries, case_ids)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if args.limit:
        entries = entries[: args.limit]
    if args.validate_only:
        payload: dict[str, Any] = {"entries": len(entries), "status": "ok"}
        if case_ids:
            payload["selected_case_ids"] = case_ids
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    output_path, markdown_output_path = resolve_report_paths(args, targeted=bool(case_ids))
    settings = get_settings()
    if not settings.github_token and not args.allow_unauthenticated:
        report = build_skipped_report(
            entries,
            reason="GITHUB_TOKEN is not configured. Use --allow-unauthenticated for a small risky run, or set GITHUB_TOKEN in .env.",
        )
    else:
        stats, details = asyncio.run(evaluate(entries, top_k=args.top_k, sleep_seconds=max(0.0, args.sleep_seconds)))
        report = build_report(stats, details)
    report = annotate_targeted_report(report, case_ids)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    if markdown_output_path:
        markdown_output_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_output_path.write_text(
            render_markdown_report(report, benchmark_path=args.benchmark, top_k=args.top_k),
            encoding="utf-8",
        )
    print(rendered)


if __name__ == "__main__":
    main()
