import argparse
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import evaluate_benchmark
from app.schemas import SearchPaperReposOutput, SearchResultItem


def _args(**overrides):
    values = {
        "case_id": [],
        "case_ids": None,
        "case_ids_file": None,
        "identity_overrides": False,
        "report_prefix": None,
        "output": None,
        "markdown_output": None,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def test_select_benchmark_entries_keeps_requested_order() -> None:
    entries = [
        {"id": "a", "paper_title": "A"},
        {"id": "b", "paper_title": "B"},
        {"id": "c", "paper_title": "C"},
    ]

    selected = evaluate_benchmark.select_benchmark_entries(entries, ["c", "a"])

    assert [entry["id"] for entry in selected] == ["c", "a"]


def test_select_benchmark_entries_reports_missing_case_id() -> None:
    with pytest.raises(ValueError, match="missing_case"):
        evaluate_benchmark.select_benchmark_entries([{"id": "known"}], ["missing_case"])


def test_selected_case_ids_from_args_combines_cli_file_and_identity_overrides(tmp_path, monkeypatch) -> None:
    case_file = tmp_path / "cases.txt"
    case_file.write_text("stable_diffusion_2022, ddpm_2020\n# comment\nllava_2023\n", encoding="utf-8")
    overrides = tmp_path / "paper_code_identity_overrides.json"
    overrides.write_text(
        json.dumps(
            [
                {"paper_id": "gaussian_splatting_2023"},
                {"paper_id": "stable_diffusion_2022"},
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(evaluate_benchmark, "DEFAULT_IDENTITY_OVERRIDES", overrides)

    case_ids = evaluate_benchmark.selected_case_ids_from_args(
        _args(
            case_id=["instant_ngp_2022"],
            case_ids="stable_diffusion_2022",
            case_ids_file=case_file,
            identity_overrides=True,
        )
    )

    assert case_ids == [
        "instant_ngp_2022",
        "stable_diffusion_2022",
        "ddpm_2020",
        "llava_2023",
        "gaussian_splatting_2023",
    ]


def test_resolve_report_paths_preserves_full_defaults_and_targets_targeted_reports() -> None:
    full_json, full_md = evaluate_benchmark.resolve_report_paths(_args(), targeted=False)
    targeted_json, targeted_md = evaluate_benchmark.resolve_report_paths(_args(), targeted=True)
    prefixed_json, prefixed_md = evaluate_benchmark.resolve_report_paths(
        _args(report_prefix="smoke_identity"),
        targeted=True,
    )

    assert full_json == evaluate_benchmark.DEFAULT_JSON_REPORT
    assert full_md == evaluate_benchmark.DEFAULT_MARKDOWN_REPORT
    assert targeted_json == evaluate_benchmark.DEFAULT_TARGETED_JSON_REPORT
    assert targeted_md == evaluate_benchmark.DEFAULT_TARGETED_MARKDOWN_REPORT
    assert prefixed_json.name == "smoke_identity_benchmark_report.json"
    assert prefixed_md.name == "smoke_identity_benchmark_report.md"


def test_render_targeted_markdown_includes_per_case_table() -> None:
    report = evaluate_benchmark.annotate_targeted_report(
        {
            "summary": {
                "total": 1,
                "attempted": 1,
                "evaluated": 1,
                "unprocessed": 0,
                "failed": 0,
                "provider_failed": 0,
                "rate_limited": 0,
                "top1_hit_rate": 1.0,
                "top3_hit_rate": 1.0,
                "official_top1_hit_rate": 1.0,
                "official_top3_hit_rate": 1.0,
                "distractor_top1_rate": 0.0,
            },
            "by_task": {},
            "failure_summary_by_task": {},
            "failure_summary_by_cause": {},
            "failure_examples": [],
            "details": [
                {
                    "id": "ddpm_2020",
                    "retrieved": ["hojonathanho/diffusion"],
                    "top1_hit": True,
                    "top3_hit": True,
                    "official_top1_hit": True,
                    "official_top3_hit": True,
                    "distractor_top1": False,
                    "failure_cause": "success",
                }
            ],
        },
        ["ddpm_2020"],
    )

    rendered = evaluate_benchmark.render_markdown_report(
        report,
        benchmark_path=Path("benchmarks/paper_repro_benchmark.json"),
        top_k=3,
    )

    assert "- Selected cases: `1`" in rendered
    assert "## Per-Case Results" in rendered
    assert "`ddpm_2020`" in rendered


def test_targeted_main_skips_without_github_token_and_writes_reports(tmp_path, monkeypatch) -> None:
    output = tmp_path / "targeted.json"
    markdown = tmp_path / "targeted.md"
    monkeypatch.setattr(
        evaluate_benchmark,
        "parse_args",
        lambda: _args(
            benchmark=Path("benchmarks/paper_repro_benchmark.json"),
            limit=None,
            case_ids="stable_diffusion_2022,ddpm_2020",
            top_k=3,
            output=output,
            markdown_output=markdown,
            sleep_seconds=0.0,
            allow_unauthenticated=False,
            validate_only=False,
        ),
    )
    monkeypatch.setattr(evaluate_benchmark, "get_settings", lambda: SimpleNamespace(github_token=None))

    evaluate_benchmark.main()

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["summary"]["status"] == "skipped"
    assert report["summary"]["selected_case_count"] == 2
    assert report["summary"]["selected_case_ids"] == ["stable_diffusion_2022", "ddpm_2020"]
    assert "GITHUB_TOKEN is not configured" in report["summary"]["reason"]
    assert "- Selected cases: `2`" in markdown.read_text(encoding="utf-8")


def test_evaluate_entry_matches_expected_repo_alias(monkeypatch) -> None:
    async def fake_search_paper_repos_tool(**kwargs):
        return SearchPaperReposOutput(
            query_analysis={  # type: ignore[arg-type]
                "raw_query": kwargs["query"],
                "source_types": ["github"],
            },
            results=[
                SearchResultItem(
                    title="PaddlePaddle/PaddleSpeech",
                    url="https://github.com/PaddlePaddle/PaddleSpeech",
                    repo="PaddlePaddle/PaddleSpeech",
                    repo_aliases=["PaddlePaddle/DeepSpeech", "PaddlePaddle/PaddleSpeech"],
                    source="github",
                    source_type="github",
                )
            ],
        )

    monkeypatch.setattr(evaluate_benchmark, "search_paper_repos_tool", fake_search_paper_repos_tool)
    detail = asyncio.run(
        evaluate_benchmark.evaluate_entry(
            {
                "id": "deepspeech2_2015",
                "paper_title": "Deep Speech 2: End-to-End Speech Recognition in English and Mandarin",
                "query": "Deep Speech 2 code",
                "task": "speech",
                "official_repos": ["PaddlePaddle/DeepSpeech"],
                "high_quality_reproduction_repos": [],
                "common_distractor_repos": [],
            },
            top_k=3,
        )
    )

    assert detail["retrieved"] == ["paddlepaddle/paddlespeech"]
    assert detail["retrieved_repo_aliases"] == [["paddlepaddle/deepspeech", "paddlepaddle/paddlespeech"]]
    assert detail["official_top1_hit"] is True
    assert detail["official_rank"] == 1


def test_evaluate_entry_counts_reproduction_identity_without_official_hit(monkeypatch) -> None:
    async def fake_search_paper_repos_tool(**kwargs):
        return SearchPaperReposOutput(
            query_analysis={  # type: ignore[arg-type]
                "raw_query": kwargs["query"],
                "source_types": ["github"],
            },
            results=[
                SearchResultItem(
                    title="benfred/implicit",
                    url="https://github.com/benfred/implicit",
                    repo="benfred/implicit",
                    source="github",
                    source_type="github",
                    identity_source="curated_override",
                    identity_confidence="medium",
                    identity_type="domain_library_implementation",
                    identity_evidence=["domain library implementation evidence"],
                    metadata={
                        "external_identity": {
                            "source": "curated_override",
                            "confidence": "medium",
                            "identity_type": "domain_library_implementation",
                        }
                    },
                )
            ],
        )

    monkeypatch.setattr(evaluate_benchmark, "search_paper_repos_tool", fake_search_paper_repos_tool)
    detail = asyncio.run(
        evaluate_benchmark.evaluate_entry(
            {
                "id": "implicit_mf_2008",
                "paper_title": "Collaborative Filtering for Implicit Feedback Datasets",
                "query": "Collaborative Filtering for Implicit Feedback Datasets paper code",
                "task": "recommender",
                "official_repos": [],
                "high_quality_reproduction_repos": ["benfred/implicit"],
                "common_distractor_repos": [],
            },
            top_k=3,
        )
    )

    assert detail["top1_hit"] is True
    assert detail["top3_hit"] is True
    assert detail["official_top1_hit"] is False
    assert detail["official_top3_hit"] is False
    assert detail["official_rank"] is None
    assert detail["acceptable_rank"] == 1
    assert detail["retrieved_identity"][0]["identity_type"] == "domain_library_implementation"
