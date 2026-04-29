from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = PROJECT_ROOT / "reports" / "benchmark_report.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "reports" / "remaining_miss_analysis.md"


EXPECTED_REPRODUCTION_MISSES = {"implicit_mf_2008", "deepfm_2017"}


OFFICIAL_RECALLED_NOT_TOP1 = {
    "nerf_2020",
    "vit_2020",
    "simclr_2020",
    "guided_diffusion_2021",
    "grounding_dino_2023",
    "monodepth2_2019",
    "orb_slam3_2020",
    "colmap_2016",
    "lightgcn_2020",
    "llava_2023",
    "ultralytics_yolov8_2023",
    "mmdetection_2019",
    "wav2vec2_2020",
    "hubert_2021",
}


@dataclass(frozen=True)
class CaseNote:
    likely_reason: str
    next_action: str
    worth_fix: str


CASE_NOTES = {
    "implicit_mf_2008": CaseNote(
        likely_reason=(
            "Benchmark target is the mature `benfred/implicit` package, while live search returns "
            "paper-title-specific reimplementations; there is no `official_repos` label to anchor direct fetch."
        ),
        next_action=(
            "If recommender coverage matters, add a separate evidence-backed reproduction identity mapping "
            "for no-official benchmark targets; do not solve this with broad alias/scoring changes."
        ),
        worth_fix="medium",
    ),
    "deepfm_2017": CaseNote(
        likely_reason=(
            "Benchmark target is the broader `shenweichen/deepctr` CTR-model library, not a repo named exactly "
            "`DeepFM`; title search therefore prefers smaller DeepFM-specific or adjacent repositories."
        ),
        next_action=(
            "Use evidence-backed reproduction identity for no-official targets if this benchmark class remains "
            "important; otherwise leave as a known reproduction-target miss."
        ),
        worth_fix="medium-high",
    ),
    "nerf_2020": CaseNote(
        likely_reason=(
            "`sxyu/pixel-nerf` is a strong related NeRF repository and outranks the older official `bmild/nerf`, "
            "which is still recalled at rank 2."
        ),
        next_action="Do not prioritize unless Top-1 becomes the main KPI; broad NeRF reranking can disturb related papers.",
        worth_fix="low",
    ),
    "vit_2020": CaseNote(
        likely_reason=(
            "An unrelated/weakly related repo occupies rank 1, while curated identity recalls "
            "`google-research/vision_transformer` at rank 2."
        ),
        next_action="Only investigate if a future score audit shows a generic collision signal that can be fixed safely.",
        worth_fix="low-medium",
    ),
    "simclr_2020": CaseNote(
        likely_reason=(
            "A third-party implementation ranks above `google-research/simclr`; the official repo is safely in top-3."
        ),
        next_action="Leave as top-3 success unless official Top-1 becomes a product requirement.",
        worth_fix="low",
    ),
    "guided_diffusion_2021": CaseNote(
        likely_reason=(
            "`mchong6/gansnroses` matches diffusion/GAN wording strongly and outranks the curated official "
            "`openai/guided-diffusion` candidate."
        ),
        next_action="Avoid broad diffusion scoring changes; consider only an identity-source top-1 policy after separate audit.",
        worth_fix="low-medium",
    ),
    "grounding_dino_2023": CaseNote(
        likely_reason=(
            "Finetuning/open variants rank above the official `idea-research/groundingdino`, which is recalled at rank 3."
        ),
        next_action="Potential future project-page identity case, but current top-3 behavior is already correct.",
        worth_fix="medium",
    ),
    "monodepth2_2019": CaseNote(
        likely_reason=(
            "Forks or ports with exact `monodepth2` naming outrank the official `nianticlabs/monodepth2` repo at rank 3."
        ),
        next_action="Only fix after a fork/port audit confirms a safe generic demotion signal.",
        worth_fix="medium",
    ),
    "orb_slam3_2020": CaseNote(
        likely_reason=(
            "ROS/wrapper repositories outrank the official `uz-slamlab/orb_slam3`, which remains recalled at rank 3."
        ),
        next_action="Low priority; robotics wrappers are useful search results and broad demotion could harm users.",
        worth_fix="low",
    ),
    "colmap_2016": CaseNote(
        likely_reason=(
            "A related multiview/stereo repo ranks above the official `colmap/colmap`; curated identity still recalls "
            "the official repo at rank 2."
        ),
        next_action="Leave as top-3 success unless a future stage explicitly optimizes official Top-1.",
        worth_fix="low",
    ),
    "lightgcn_2020": CaseNote(
        likely_reason=(
            "Two same-name implementations outrank the official `gusye1234/lightgcn-pytorch`; one labeled distractor "
            "appears at rank 2 but not rank 1."
        ),
        next_action="Worth a targeted score audit because it is the only remaining failure with a labeled distractor in top-3.",
        worth_fix="medium-high",
    ),
    "llava_2023": CaseNote(
        likely_reason=(
            "Adjacent LLaVA-family projects (`llava-med`, SmartEdit) rank above the official `haotian-liu/llava`, "
            "which curated identity recalls at rank 3."
        ),
        next_action="Medium priority only if official Top-1 matters; family-project ambiguity makes broad ranking risky.",
        worth_fix="medium",
    ),
    "ultralytics_yolov8_2023": CaseNote(
        likely_reason=(
            "A YOLOv8 implementation repo outranks the official `ultralytics/ultralytics`, which is recalled at rank 2."
        ),
        next_action="Leave as top-3 success; a generic YOLO official-owner boost could affect YOLOv5/v7/v8 balance.",
        worth_fix="low-medium",
    ),
    "mmdetection_2019": CaseNote(
        likely_reason=(
            "`allenai/mmdetection` shares the exact repo slug and outranks official `open-mmlab/mmdetection`; this looks "
            "like an owner/fork/mirror collision rather than an identity miss."
        ),
        next_action="High-value candidate for a read-only fork/mirror metadata audit before any future ranking change.",
        worth_fix="high",
    ),
    "wav2vec2_2020": CaseNote(
        likely_reason=(
            "Title-specific wav2vec repositories outrank the broad official `facebookresearch/fairseq` monorepo at rank 3."
        ),
        next_action="Leave unless optimizing official Top-1 for monorepo-hosted implementations becomes a priority.",
        worth_fix="low-medium",
    ),
    "hubert_2021": CaseNote(
        likely_reason=(
            "Title-specific HuBERT repositories outrank the broad official `facebookresearch/fairseq` monorepo at rank 3."
        ),
        next_action="Treat together with `wav2vec2_2020`; monorepo ranking is a policy decision, not a recall problem.",
        worth_fix="low-medium",
    ),
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _repo_list(values: list[str]) -> str:
    return ", ".join(f"`{value}`" for value in values) if values else "`none`"


def _target_repo(detail: dict[str, Any]) -> list[str]:
    return detail.get("official_repos") or detail.get("high_quality_reproduction_repos") or []


def _case_type(case_id: str) -> str:
    if case_id in EXPECTED_REPRODUCTION_MISSES:
        return "expected reproduction miss"
    if case_id in OFFICIAL_RECALLED_NOT_TOP1:
        return "official recalled, not top-1"
    return "other"


def _render_case_row(detail: dict[str, Any]) -> str:
    case_id = detail["id"]
    note = CASE_NOTES[case_id]
    rank = detail.get("official_rank") or detail.get("acceptable_rank") or "not recalled"
    return (
        f"| `{case_id}` | {_case_type(case_id)} | `{rank}` | {_repo_list(_target_repo(detail))} | "
        f"{_repo_list(detail.get('retrieved') or [])} | {note.likely_reason} | `{note.worth_fix}` | {note.next_action} |"
    )


def render_markdown(report: dict[str, Any]) -> str:
    details = {detail["id"]: detail for detail in report.get("details", [])}
    expected_misses = [details[case_id] for case_id in sorted(EXPECTED_REPRODUCTION_MISSES)]
    official_not_top1 = [details[case_id] for case_id in sorted(OFFICIAL_RECALLED_NOT_TOP1)]
    official_rank_counts: dict[str, int] = {}
    for detail in official_not_top1:
        key = str(detail.get("official_rank"))
        official_rank_counts[key] = official_rank_counts.get(key, 0) + 1
    summary = report.get("summary", {})
    lines = [
        "# Remaining Miss Analysis",
        "",
        "## Scope",
        "",
        "- Source report: `reports/benchmark_report.json`",
        f"- Full benchmark Top-1 / Top-3: `{summary.get('top1_hit_rate')}` / `{summary.get('top3_hit_rate')}`",
        (
            "- Official Top-1 / Official Top-3: "
            f"`{summary.get('official_top1_hit_rate')}` / `{summary.get('official_top3_hit_rate')}`"
        ),
        f"- Distractor ranked #1: `{summary.get('distractor_top1_rate')}`",
        f"- Expected-reproduction misses analyzed: `{len(expected_misses)}`",
        f"- Official-recalled-not-top1 cases analyzed: `{len(official_not_top1)}`",
        "",
        "## Aggregate Findings",
        "",
        "- Official recall is no longer the bottleneck: every case with `official_repos` has the official repo in top-3.",
        "- Remaining Top-3 misses are both no-official-label recommender cases where the target is a reproduction/library repo.",
        (
            "- Official-not-top1 cases split evenly: "
            f"`{official_rank_counts.get('2', 0)}` at official rank 2 and "
            f"`{official_rank_counts.get('3', 0)}` at official rank 3."
        ),
        "- Most official-not-top1 cases are adjacent-project, fork/port, monorepo, or same-slug owner collisions; broad scoring changes would be risky.",
        "",
        "## Expected-Reproduction Misses",
        "",
        "| Case | Type | Rank | Target repo | Retrieved top-3 | Why it missed | Worth fixing? | Minimal next action |",
        "|---|---|---:|---|---|---|---|---|",
    ]
    lines.extend(_render_case_row(detail) for detail in expected_misses)
    lines.extend(
        [
            "",
            "## Official Recalled But Not Top-1",
            "",
            "| Case | Type | Official rank | Official repo | Retrieved top-3 | Why not top-1 | Worth fixing? | Minimal next action |",
            "|---|---|---:|---|---|---|---|---|",
        ]
    )
    lines.extend(_render_case_row(detail) for detail in official_not_top1)
    lines.extend(
        [
            "",
            "## Next-Round Recommendations",
            "",
            "1. Start with `mmdetection_2019` and `lightgcn_2020` as read-only audits: they have the clearest owner/fork/distractor collision signals and do not require Papers with Code.",
            "2. If improving recommender Top-3 matters, design a small evidence-backed reproduction-identity path for no-official-label cases (`implicit_mf_2008`, `deepfm_2017`) instead of changing general retrieval or scoring.",
            "3. Defer broad Top-1 ranking changes until there is a separate score audit; current Official Top-3 is already `0.9434` and distractor ranked #1 is `0.0000`.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze remaining benchmark misses without running providers.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = _load_json(args.report)
    rendered = render_markdown(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
