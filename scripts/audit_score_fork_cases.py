from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.query_analyzer import analyze_query
from app.providers.github import GitHubProvider

from audit_candidate_scores import _fetch_scored_repo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BENCHMARK = PROJECT_ROOT / "benchmarks" / "paper_repro_benchmark.json"
DEFAULT_REPORT = PROJECT_ROOT / "reports" / "benchmark_report.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "reports" / "score_fork_audit.md"
TARGET_CASE_IDS = ["mmdetection_2019", "lightgcn_2020"]


@dataclass(frozen=True)
class AuditPolicy:
    top1_category: str
    interpretation: str
    worth_fix: str
    next_action: str


CASE_POLICY = {
    "mmdetection_2019": AuditPolicy(
        top1_category="same-slug owner collision",
        interpretation=(
            "`allenai/mmdetection` uses the exact `mmdetection` slug under a canonical research owner, so it can look "
            "as relevant as `open-mmlab/mmdetection` even though the benchmark labels OpenMMLab as official."
        ),
        worth_fix="yes, small targeted fix is worth considering",
        next_action=(
            "Audit whether `allenai/mmdetection` is a fork/mirror/downstream copy; if confirmed, consider a narrow "
            "fork/mirror or canonical-owner tie-breaker rather than changing broad scoring weights."
        ),
    ),
    "lightgcn_2020": AuditPolicy(
        top1_category="same-slug implementation collision",
        interpretation=(
            "`lucapantea/lightgcn` has the exact paper/project slug and ranks above the official "
            "`gusye1234/lightgcn-pytorch`; the labeled distractor `kuandeng/lightgcn` appears at rank 2, not rank 1."
        ),
        worth_fix="maybe, but only after a targeted distractor/fork audit",
        next_action=(
            "Treat as a recommender-specific collision: first inspect same-slug third-party implementations and the "
            "rank-2 labeled distractor before adding any ranking policy."
        ),
    ),
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_repo(repo: str | None) -> str:
    return (repo or "").strip().casefold()


def _repo_list(values: list[str]) -> str:
    return ", ".join(f"`{value}`" for value in values) if values else "`none`"


def _score_value(score: dict[str, Any] | None, key: str) -> float:
    if not score:
        return 0.0
    return float(score.get(key) or 0.0)


def _delta(top1: dict[str, Any] | None, official: dict[str, Any] | None, key: str) -> float:
    return round(_score_value(top1, key) - _score_value(official, key), 4)


def _score_summary(score: dict[str, Any] | None) -> str:
    if not score:
        return "`unavailable`"
    return (
        f"`score={score.get('score', 0):.4f}`, `query={score.get('query_score', 0):.4f}`, "
        f"`assets={score.get('asset_score', 0):.4f}`, `freshness={score.get('freshness', 0):.4f}`, "
        f"`popularity={score.get('popularity', 0):.4f}`, `role_bonus={score.get('role_bonus', 0):.4f}`, "
        f"`cap={score.get('cap_reason') or 'none'}`"
    )


def _dominant_score_reasons(top1_score: dict[str, Any] | None, official_score: dict[str, Any] | None) -> list[str]:
    components = [
        ("query_score", "query/name identity"),
        ("asset_score", "asset signals"),
        ("freshness", "freshness"),
        ("popularity", "popularity"),
        ("tech_score", "tech stack"),
        ("role_bonus", "role/canonical bonus"),
    ]
    reasons = [
        f"{label} +{_delta(top1_score, official_score, key):.4f}"
        for key, label in components
        if _delta(top1_score, official_score, key) >= 0.03
    ]
    if official_score and official_score.get("cap_reason"):
        reasons.append(f"official cap: {official_score['cap_reason']}")
    return reasons or ["component scores are close; ordering likely comes from small aggregate deltas"]


async def _repo_payload(provider: GitHubProvider, repo: str) -> dict[str, Any] | None:
    if "/" not in repo:
        return None
    owner, name = repo.split("/", 1)
    return await provider._fetch_repository(owner, name)


def _repo_metadata(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {
            "fork": None,
            "parent": None,
            "source": None,
            "archived": None,
            "stars": None,
            "forks": None,
            "description": "",
        }
    parent = payload.get("parent") if isinstance(payload.get("parent"), dict) else {}
    source = payload.get("source") if isinstance(payload.get("source"), dict) else {}
    return {
        "fork": payload.get("fork"),
        "parent": parent.get("full_name"),
        "source": source.get("full_name"),
        "archived": payload.get("archived"),
        "stars": payload.get("stargazers_count"),
        "forks": payload.get("forks_count"),
        "description": payload.get("description") or "",
    }


async def audit_cases(benchmark_path: Path, report_path: Path) -> list[dict[str, Any]]:
    benchmark = {entry["id"]: entry for entry in _load_json(benchmark_path)}
    details = {entry["id"]: entry for entry in _load_json(report_path).get("details", [])}
    provider = GitHubProvider()
    audits: list[dict[str, Any]] = []
    for case_id in TARGET_CASE_IDS:
        entry = benchmark[case_id]
        detail = details[case_id]
        analysis = analyze_query(
            entry["query"],
            paper_title=entry.get("paper_title"),
            task=entry.get("task"),
            source_types=["github"],
        )
        top3 = [_normalize_repo(repo) for repo in detail.get("retrieved") or []]
        official_repos = [_normalize_repo(repo) for repo in detail.get("official_repos") or []]
        top1 = top3[0] if top3 else ""
        official = official_repos[0] if official_repos else ""
        top1_score = await _fetch_scored_repo(provider, analysis, top1)
        official_score = await _fetch_scored_repo(provider, analysis, official)
        top1_payload = await _repo_payload(provider, top1)
        official_payload = await _repo_payload(provider, official)
        audits.append(
            {
                "id": case_id,
                "paper_title": entry.get("paper_title"),
                "top3": top3,
                "official_repos": official_repos,
                "official_rank": detail.get("official_rank"),
                "distractor_rank": detail.get("distractor_rank"),
                "common_distractors": [_normalize_repo(repo) for repo in detail.get("common_distractor_repos") or []],
                "top1": top1,
                "top1_score": top1_score,
                "official_score": official_score,
                "top1_metadata": _repo_metadata(top1_payload),
                "official_metadata": _repo_metadata(official_payload),
                "dominant_score_reasons": _dominant_score_reasons(top1_score, official_score),
                "policy": CASE_POLICY[case_id],
            }
        )
    return audits


def _metadata_text(metadata: dict[str, Any]) -> str:
    return (
        f"fork=`{metadata['fork']}`, parent=`{metadata['parent'] or 'none'}`, "
        f"source=`{metadata['source'] or 'none'}`, stars=`{metadata['stars']}`, "
        f"forks=`{metadata['forks']}`, archived=`{metadata['archived']}`"
    )


def render_markdown(audits: list[dict[str, Any]]) -> str:
    lines = [
        "# Score / Fork Audit",
        "",
        "## Scope",
        "",
        "- Source report: `reports/benchmark_report.json`",
        "- Target cases: `mmdetection_2019`, `lightgcn_2020`",
        "- This is a read-only audit: no scorer, retrieval, provider, or identity logic was changed.",
        "- The script fetches current GitHub metadata for the reported top-1 and official repos only; it does not run the full benchmark.",
        "",
        "## Summary",
        "",
        "| Case | Current top-3 | Official rank | Top-1 category | Why top-1 beats official | Worth next fix? |",
        "|---|---|---:|---|---|---|",
    ]
    for audit in audits:
        policy = audit["policy"]
        lines.append(
            f"| `{audit['id']}` | {_repo_list(audit['top3'])} | `{audit['official_rank']}` | "
            f"{policy.top1_category} | {'; '.join(audit['dominant_score_reasons'])}. {policy.interpretation} | "
            f"{policy.worth_fix} |"
        )
    lines.extend(["", "## Case Details", ""])
    for audit in audits:
        policy = audit["policy"]
        top1_is_labeled_distractor = audit["top1"] in set(audit["common_distractors"])
        lines.extend(
            [
                f"### `{audit['id']}`",
                "",
                f"- Paper: {audit['paper_title']}",
                f"- Current top-3: {_repo_list(audit['top3'])}",
                f"- Official repo: {_repo_list(audit['official_repos'])}; rank: `{audit['official_rank']}`",
                f"- Labeled distractors: {_repo_list(audit['common_distractors'])}; distractor rank: `{audit['distractor_rank'] or 'none'}`",
                f"- Top-1 classification: `{policy.top1_category}`; top-1 is labeled distractor: `{'yes' if top1_is_labeled_distractor else 'no'}`",
                f"- Top-1 metadata: {_metadata_text(audit['top1_metadata'])}",
                f"- Official metadata: {_metadata_text(audit['official_metadata'])}",
                f"- Top-1 score: {_score_summary(audit['top1_score'])}",
                f"- Official score: {_score_summary(audit['official_score'])}",
                f"- Why top-1 wins: {'; '.join(audit['dominant_score_reasons'])}. {policy.interpretation}",
                f"- Worth fixing next: {policy.worth_fix}",
                f"- Minimal next action: {policy.next_action}",
                "",
            ]
        )
    lines.extend(
        [
            "## Minimal Next-Fix Suggestions",
            "",
            "1. Start with `mmdetection_2019`: verify whether `allenai/mmdetection` is a fork/mirror/downstream copy, then consider a narrow same-slug owner-collision tie-breaker only if the evidence is stable.",
            "2. For `lightgcn_2020`, avoid broad scoring changes; first audit same-slug recommender implementations and the rank-2 labeled distractor `kuandeng/lightgcn`.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only score/fork audit for selected benchmark cases.")
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    audits = asyncio.run(audit_cases(args.benchmark, args.report))
    rendered = render_markdown(audits)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(json.dumps({"cases": [audit["id"] for audit in audits], "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
