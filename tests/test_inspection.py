from app.core.inspection import build_inspection_signals


def test_deep_inspection_detects_reproduction_signals() -> None:
    signals = build_inspection_signals(
        {
            "tree_paths": [
                "tools/train.py",
                "tools/eval.py",
                "configs/coco.yaml",
                "requirements.txt",
                "poetry.lock",
            ]
        },
        "Run training and evaluation. Download checkpoint from https://example.com/model_weights.pth. arXiv:2304.02643",
        config_texts={"configs/coco.yaml": "dataset: COCO\ndata_root: /datasets/coco"},
    )

    assert signals["training_entries"] == ["tools/train.py"]
    assert signals["evaluation_entries"] == ["tools/eval.py"]
    assert signals["environment_lockfiles"] == ["poetry.lock"]
    assert signals["checkpoint_links"] == ["https://example.com/model_weights.pth"]
    assert "configs/coco.yaml: coco" in signals["config_dataset_refs"]
    assert signals["paper_links"]["arxiv_ids"] == ["2304.02643"]
    assert signals["has_reproduction_instruction"] is True
    assert signals["training_readiness"]["level"] == "ready"
    assert signals["evaluation_readiness"]["level"] == "ready"
    assert signals["environment_reproducibility"]["level"] == "locked"
    assert signals["paper_identity_confidence"]["level"] == "high"
