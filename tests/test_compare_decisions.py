from app.core.service import PaperReproductionIntelligenceService
from app.schemas import ComparePaperRepoItem, InspectPaperRepoOutput


def test_compare_decision_helpers_pick_actionable_roles() -> None:
    service = PaperReproductionIntelligenceService()
    direct = ComparePaperRepoItem(
        repo="owner/direct",
        score=0.8,
        risk_level="low",
        repo_role="reproduction",
        decision_tags=["direct_reproduction_candidate", "baseline_candidate"],
    )
    official = ComparePaperRepoItem(
        repo="owner/official",
        score=0.7,
        risk_level="medium",
        repo_role="official_implementation",
        decision_tags=["method_reference"],
    )

    assert service._best_direct_reproduction([official, direct]) == "owner/direct"
    assert service._best_method_reference([official, direct]) == "owner/official"
    assert service._best_baseline([official, direct]) == "owner/direct"


def test_decision_tags_use_deep_inspection_signals() -> None:
    service = PaperReproductionIntelligenceService()
    item = InspectPaperRepoOutput(
        repo="owner/repro",
        repo_role="implementation",
        score=0.72,
        risk_level="medium",
        reproduction_assets={"has_training_code": True, "has_eval_code": True},
        inspection_signals={
            "evaluation_entries": ["eval.py"],
            "has_reproduction_instruction": True,
            "environment_lockfiles": ["poetry.lock"],
            "training_readiness": {"level": "ready", "reason": "train.py", "evidence": ["train.py"]},
            "evaluation_readiness": {"level": "ready", "reason": "eval.py", "evidence": ["eval.py"]},
            "environment_reproducibility": {"level": "locked", "reason": "poetry.lock", "evidence": ["poetry.lock"]},
            "paper_identity_confidence": {"level": "high", "reason": "arXiv", "evidence": ["arXiv:1234.5678"]},
        },
    )

    tags = service._decision_tags(item)

    assert "direct_reproduction_candidate" in tags
    assert "baseline_candidate" in tags
    assert "has_reproduction_instruction" in tags
    assert "has_environment_lockfile" in tags
    assert "has_paper_identity_evidence" in tags


def test_selection_reasons_explain_real_inspection_signals() -> None:
    service = PaperReproductionIntelligenceService()
    item = ComparePaperRepoItem(
        repo="owner/repro",
        score=0.8,
        risk_level="low",
        decision_tags=["direct_reproduction_candidate"],
        best_for=["training code"],
        reason="training=ready, evaluation=ready",
        training_readiness={"level": "ready", "reason": "train.py", "evidence": ["train.py"]},
        evaluation_readiness={"level": "ready", "reason": "eval.py", "evidence": ["eval.py"]},
        environment_reproducibility={"level": "locked", "reason": "poetry.lock", "evidence": ["poetry.lock"]},
        paper_identity_confidence={"level": "high", "reason": "arXiv", "evidence": ["arXiv:1234.5678"]},
    )

    reason = service._selection_reason("owner/repro", [item], purpose="direct reproduction")

    assert "training=ready" in reason
    assert "evaluation=ready" in reason
    assert "direct_reproduction_candidate" in reason
