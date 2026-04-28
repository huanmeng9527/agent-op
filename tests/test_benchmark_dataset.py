from pathlib import Path

from scripts.evaluate_benchmark import load_benchmark


def test_benchmark_seed_has_required_labels() -> None:
    entries = load_benchmark(Path("benchmarks/paper_repro_benchmark.json"))

    assert len(entries) >= 50
    for entry in entries:
        assert entry["paper_title"]
        assert isinstance(entry["official_repos"], list)
        assert isinstance(entry["high_quality_reproduction_repos"], list)
        assert isinstance(entry["common_distractor_repos"], list)
        assert "has_training_code" in entry["expected_assets"]
        assert "has_eval_code" in entry["expected_assets"]
