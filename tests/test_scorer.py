from app.core.query_analyzer import analyze_query
from app.ranking.scorer import classify_repo_role, detect_reproduction_assets, infer_tech_stack, score_provider_result
from app.schemas import ProviderSearchResult


def test_unofficial_is_not_classified_as_official() -> None:
    assets = detect_reproduction_assets({}, "")

    assert classify_repo_role("Unofficial reimplementation of a paper", assets) == "reproduction"
    assert classify_repo_role("Official implementation for our paper", assets) == "official_implementation"


def test_research_org_repo_can_be_official_candidate() -> None:
    assets = detect_reproduction_assets({"root_paths": ["notebooks/demo.ipynb", "requirements.txt"]}, "")

    assert classify_repo_role("facebookresearch segment anything", assets) == "official_implementation"


def test_asset_detection_avoids_common_false_positives() -> None:
    assets = detect_reproduction_assets(
        {"root_paths": ["tests/test_api.py", "metadata.json", "docs/results.md"]},
        "",
    )

    assert assets["has_eval_code"] is False
    assert assets["has_config"] is False
    assert assets["has_results"] is False


def test_asset_detection_finds_reproduction_structure() -> None:
    assets = detect_reproduction_assets(
        {"root_paths": ["train.py", "configs/default.yaml", "requirements.txt", "scripts/eval.py"]},
        "Download data and pretrained weights before running evaluation.",
    )

    assert assets["has_training_code"] is True
    assert assets["has_eval_code"] is True
    assert assets["has_config"] is True
    assert assets["has_requirements"] is True
    assert assets["has_dataset_doc"] is True
    assert assets["has_checkpoint_hint"] is True


def test_tech_stack_uses_term_boundaries() -> None:
    assert infer_tech_stack("transformer implementation") == []
    assert infer_tech_stack("R implementation with PyTorch") == ["pytorch", "r"]


def test_collection_result_is_score_capped() -> None:
    item = ProviderSearchResult(
        title="owner/awesome-paper-list",
        url="https://github.com/owner/awesome-paper-list",
        source="github",
        source_type="github",
        snippet="Awesome papers and reading list for Segment Anything",
        metadata={
            "full_name": "owner/awesome-paper-list",
            "description": "Awesome papers and reading list for Segment Anything",
            "stargazers_count": 50000,
            "updated_at": "2026-01-01T00:00:00Z",
            "root_paths": ["README.md", "requirements.txt", "configs/default.yaml", "weights/model.pth"],
            "readme_text": "Segment Anything paper code list",
        },
    )

    explanation = score_provider_result(analyze_query("Segment Anything paper code", paper_title="Segment Anything"), item)

    assert explanation.repo_role == "paper_collection"
    assert explanation.cap_reason == "paper_collection_cap"
    assert explanation.score <= 0.68


def test_reference_utility_explains_reproduction_assets() -> None:
    item = ProviderSearchResult(
        title="owner/paper-repro",
        url="https://github.com/owner/paper-repro",
        source="github",
        source_type="github",
        snippet="Unofficial reproduction with training and evaluation",
        metadata={
            "full_name": "owner/paper-repro",
            "root_paths": ["train.py", "eval.py", "requirements.txt", "configs/default.yaml"],
            "readme_text": "Unofficial reproduction. Download dataset and pretrained weights.",
        },
    )

    explanation = score_provider_result(analyze_query("paper reproduction pytorch"), item)

    assert explanation.repo_role == "reproduction"
    assert "training pipeline reference" in explanation.reference_utility
    assert "evaluation and metric reference" in explanation.reference_utility


def test_exact_repo_name_match_boosts_paper_identity() -> None:
    analysis = analyze_query("Segment Anything paper code pytorch", paper_title="Segment Anything")
    exact = ProviderSearchResult(
        title="facebookresearch/segment-anything",
        url="https://github.com/facebookresearch/segment-anything",
        source="github",
        source_type="github",
        snippet="Code for running inference with Segment Anything",
        metadata={
            "full_name": "facebookresearch/segment-anything",
            "owner": "facebookresearch",
            "stargazers_count": 100,
            "updated_at": "2025-01-01T00:00:00Z",
            "root_paths": ["requirements.txt"],
            "readme_text": "Segment Anything model inference",
        },
    )
    derivative = ProviderSearchResult(
        title="owner/grounded-segment-anything",
        url="https://github.com/owner/grounded-segment-anything",
        source="github",
        source_type="github",
        snippet="A derivative project using Segment Anything",
        metadata={
            "full_name": "owner/grounded-segment-anything",
            "stargazers_count": 100,
            "updated_at": "2025-01-01T00:00:00Z",
            "root_paths": ["requirements.txt"],
            "readme_text": "Segment Anything model inference",
        },
    )

    exact_score = score_provider_result(analysis, exact).score
    derivative_score = score_provider_result(analysis, derivative).score

    assert exact_score > derivative_score


def test_canonical_research_org_alias_boosts_official_repo() -> None:
    analysis = analyze_query(
        "StyleGAN2 ADA Training Generative Adversarial Networks with Limited Data paper code pytorch",
        paper_title="Training Generative Adversarial Networks with Limited Data",
    )
    official = ProviderSearchResult(
        title="NVlabs/stylegan2-ada-pytorch",
        url="https://github.com/NVlabs/stylegan2-ada-pytorch",
        source="github",
        source_type="github",
        snippet="Official PyTorch implementation",
        metadata={
            "full_name": "NVlabs/stylegan2-ada-pytorch",
            "owner": "NVlabs",
            "stargazers_count": 100,
            "updated_at": "2025-01-01T00:00:00Z",
            "root_paths": ["train.py", "requirements.txt"],
            "readme_text": "Official code for Training Generative Adversarial Networks with Limited Data.",
        },
    )
    non_canonical = official.model_copy(
        update={
            "title": "owner/stylegan2-ada-pytorch",
            "metadata": {**official.metadata, "full_name": "owner/stylegan2-ada-pytorch", "owner": "owner"},
        }
    )

    explanation = score_provider_result(analysis, official)
    non_canonical_score = score_provider_result(analysis, non_canonical).score

    assert "canonical research-org repository exactly matches a short paper alias" in explanation.positive_evidence
    assert explanation.score > non_canonical_score


def test_exact_canonical_alias_scores_above_prefix_match() -> None:
    analysis = analyze_query(
        "DINO Emerging Properties in Self-Supervised Vision Transformers paper code pytorch",
        paper_title="Emerging Properties in Self-Supervised Vision Transformers",
    )
    exact = ProviderSearchResult(
        title="facebookresearch/dino",
        url="https://github.com/facebookresearch/dino",
        source="github",
        source_type="github",
        snippet="PyTorch implementation for DINO self-supervised learning",
        metadata={
            "full_name": "facebookresearch/dino",
            "owner": "facebookresearch",
            "stargazers_count": 100,
            "updated_at": "2025-01-01T00:00:00Z",
            "root_paths": ["main_dino.py", "eval_linear.py", "requirements.txt", "configs/default.yaml"],
            "readme_text": "Training and evaluation code for DINO.",
        },
    )
    prefix = exact.model_copy(
        update={
            "title": "facebookresearch/dinov3",
            "metadata": {**exact.metadata, "full_name": "facebookresearch/dinov3"},
        }
    )

    exact_explanation = score_provider_result(analysis, exact)
    prefix_explanation = score_provider_result(analysis, prefix)

    assert "canonical research-org repository exactly matches a short paper alias" in exact_explanation.positive_evidence
    assert exact_explanation.score > prefix_explanation.score


def test_canonical_official_repo_is_not_over_capped_for_archival_status() -> None:
    analysis = analyze_query(
        "DINO Emerging Properties in Self-Supervised Vision Transformers paper code pytorch",
        paper_title="Emerging Properties in Self-Supervised Vision Transformers",
    )
    item = ProviderSearchResult(
        title="facebookresearch/dino",
        url="https://github.com/facebookresearch/dino",
        source="github",
        source_type="github",
        snippet="Official implementation for DINO",
        metadata={
            "full_name": "facebookresearch/dino",
            "owner": "facebookresearch",
            "archived": True,
            "stargazers_count": 1000,
            "updated_at": "2025-01-01T00:00:00Z",
            "root_paths": ["README.md"],
            "readme_text": "Official implementation for DINO self-supervised learning.",
        },
    )

    explanation = score_provider_result(analysis, item)

    assert explanation.repo_role == "official_implementation"
    assert explanation.cap_reason is None
    assert explanation.score >= 0.75


def test_archived_canonical_exact_alias_is_retained_above_prefix_variants() -> None:
    analysis = analyze_query(
        "DINO Emerging Properties in Self-Supervised Vision Transformers paper code pytorch ICCV 2021",
        paper_title="Emerging Properties in Self-Supervised Vision Transformers",
    )
    official = ProviderSearchResult(
        title="facebookresearch/dino",
        url="https://github.com/facebookresearch/dino",
        source="github",
        source_type="github",
        snippet="PyTorch implementation and pretrained models for DINO",
        metadata={
            "full_name": "facebookresearch/dino",
            "owner": "facebookresearch",
            "archived": True,
            "stargazers_count": 7500,
            "updated_at": "2024-01-01T00:00:00Z",
            "root_paths": ["main_dino.py", "eval_linear.py", "requirements.txt"],
            "readme_text": "PyTorch implementation and pretrained models for DINO.",
        },
    )
    variants = [
        official.model_copy(
            update={
                "title": "facebookresearch/dinov3",
                "metadata": {
                    **official.metadata,
                    "full_name": "facebookresearch/dinov3",
                    "archived": False,
                    "stargazers_count": 10000,
                    "readme_text": "DINOv3 self-supervised vision transformer models.",
                },
            }
        ),
        official.model_copy(
            update={
                "title": "idea-research/dino",
                "metadata": {
                    **official.metadata,
                    "full_name": "idea-research/dino",
                    "owner": "idea-research",
                    "archived": False,
                    "stargazers_count": 2800,
                    "readme_text": "DINO detection model implementation.",
                },
            }
        ),
        official.model_copy(
            update={
                "title": "idea-research/groundingdino",
                "metadata": {
                    **official.metadata,
                    "full_name": "idea-research/groundingdino",
                    "owner": "idea-research",
                    "archived": False,
                    "stargazers_count": 10000,
                    "readme_text": "GroundingDINO object detection implementation.",
                },
            }
        ),
    ]

    ranked = sorted([official, *variants], key=lambda item: score_provider_result(analysis, item).score, reverse=True)
    official_explanation = score_provider_result(analysis, official)

    assert "facebookresearch/dino" in [
        item.metadata["full_name"]
        for item in ranked[:3]
    ]
    assert official_explanation.cap_reason is None
    assert official_explanation.score >= 0.70
    assert "archived canonical research-org exact alias retained above same-prefix variants" in official_explanation.positive_evidence


def test_ordinary_archived_model_zoo_still_uses_archived_cap() -> None:
    item = ProviderSearchResult(
        title="owner/checkpoint-zoo",
        url="https://github.com/owner/checkpoint-zoo",
        source="github",
        source_type="github",
        snippet="Archived model zoo and pretrained weights for vision models",
        metadata={
            "full_name": "owner/checkpoint-zoo",
            "owner": "owner",
            "archived": True,
            "stargazers_count": 10000,
            "updated_at": "2025-01-01T00:00:00Z",
            "root_paths": ["README.md", "weights/model.pth"],
            "readme_text": "Model zoo with checkpoint and pretrained weights only.",
        },
    )

    explanation = score_provider_result(analyze_query("paper code pytorch"), item)

    assert explanation.cap_reason == "archived_cap"
    assert explanation.score <= 0.60


def test_archived_same_slug_candidate_needs_explicit_official_evidence_for_cap_protection() -> None:
    analysis = analyze_query(
        "MMDetection Open MMLab Detection Toolbox and Benchmark paper code",
        paper_title="MMDetection: Open MMLab Detection Toolbox and Benchmark",
    )
    fork_like = ProviderSearchResult(
        title="allenai/mmdetection",
        url="https://github.com/allenai/mmdetection",
        source="github",
        source_type="github",
        snippet="MMDetection object detection toolbox",
        metadata={
            "full_name": "allenai/mmdetection",
            "owner": "allenai",
            "archived": True,
            "stargazers_count": 0,
            "updated_at": "2026-01-01T00:00:00Z",
            "root_paths": ["tools/train.py", "tools/test.py", "configs/default.py", "requirements.txt"],
            "readme_text": "MMDetection object detection toolbox based on PyTorch.",
        },
    )
    canonical = fork_like.model_copy(
        update={
            "title": "open-mmlab/mmdetection",
            "metadata": {
                **fork_like.metadata,
                "full_name": "open-mmlab/mmdetection",
                "owner": "open-mmlab",
                "archived": False,
                "stargazers_count": 30000,
            },
        }
    )

    fork_explanation = score_provider_result(analysis, fork_like)
    canonical_explanation = score_provider_result(analysis, canonical)

    assert fork_explanation.cap_reason == "archived_cap"
    assert "archived same-slug candidate lacks explicit official evidence" in fork_explanation.negative_evidence
    assert canonical_explanation.score > fork_explanation.score


def test_archived_fork_flag_without_official_evidence_is_not_protected() -> None:
    analysis = analyze_query(
        "DINO Emerging Properties in Self-Supervised Vision Transformers paper code pytorch ICCV 2021",
        paper_title="Emerging Properties in Self-Supervised Vision Transformers",
    )
    fork_like = ProviderSearchResult(
        title="facebookresearch/dino",
        url="https://github.com/facebookresearch/dino",
        source="github",
        source_type="github",
        snippet="Archived fork of DINO experiments",
        metadata={
            "full_name": "facebookresearch/dino",
            "owner": "facebookresearch",
            "archived": True,
            "fork": True,
            "stargazers_count": 100,
            "updated_at": "2025-01-01T00:00:00Z",
            "root_paths": ["train.py", "eval.py", "requirements.txt"],
            "readme_text": "Archived fork of DINO experiments.",
        },
    )

    explanation = score_provider_result(analysis, fork_like)

    assert explanation.cap_reason == "archived_cap"
    assert "archived canonical research-org exact alias retained above same-prefix variants" not in explanation.positive_evidence


def test_non_archived_third_party_same_slug_is_not_archived_tiebroken() -> None:
    analysis = analyze_query(
        "LightGCN Simplifying and Powering Graph Convolution Network for Recommendation code",
        paper_title="LightGCN: Simplifying and Powering Graph Convolution Network for Recommendation",
    )
    item = ProviderSearchResult(
        title="lucapantea/lightgcn",
        url="https://github.com/lucapantea/lightgcn",
        source="github",
        source_type="github",
        snippet="LightGCN implementation with training and evaluation",
        metadata={
            "full_name": "lucapantea/lightgcn",
            "owner": "lucapantea",
            "archived": False,
            "stargazers_count": 5,
            "updated_at": "2026-01-01T00:00:00Z",
            "root_paths": ["train.py", "eval.py", "requirements.txt", "config.yaml"],
            "readme_text": "LightGCN implementation with training and evaluation.",
        },
    )

    explanation = score_provider_result(analysis, item)

    assert explanation.cap_reason != "archived_cap"
    assert "archived same-slug candidate lacks explicit official evidence" not in explanation.negative_evidence


def test_non_official_identity_does_not_trigger_archived_official_protection() -> None:
    analysis = analyze_query(
        "DINO Emerging Properties in Self-Supervised Vision Transformers paper code pytorch ICCV 2021",
        paper_title="Emerging Properties in Self-Supervised Vision Transformers",
    )
    item = ProviderSearchResult(
        title="facebookresearch/dino",
        url="https://github.com/facebookresearch/dino",
        source="github",
        source_type="github",
        snippet="Domain library implementation with training and evaluation",
        metadata={
            "full_name": "facebookresearch/dino",
            "owner": "facebookresearch",
            "archived": True,
            "stargazers_count": 1000,
            "updated_at": "2025-01-01T00:00:00Z",
            "root_paths": ["train.py", "eval.py", "requirements.txt"],
            "readme_text": "Domain library implementation with training and evaluation.",
            "external_identity": {
                "source": "curated_override",
                "confidence": "high",
                "identity_type": "domain_library_implementation",
            },
        },
    )

    explanation = score_provider_result(analysis, item)

    assert explanation.cap_reason == "archived_cap"
    assert "archived canonical research-org exact alias retained above same-prefix variants" not in explanation.positive_evidence


def test_canonical_official_library_is_not_demoted_to_paper_collection() -> None:
    analysis = analyze_query(
        "Transformers State-of-the-Art Natural Language Processing library paper code",
        paper_title="Transformers: State-of-the-Art Natural Language Processing",
    )
    item = ProviderSearchResult(
        title="huggingface/transformers",
        url="https://github.com/huggingface/transformers",
        source="github",
        source_type="github",
        snippet="State-of-the-art machine learning for PyTorch, TensorFlow, and JAX.",
        metadata={
            "full_name": "huggingface/transformers",
            "owner": "huggingface",
            "stargazers_count": 1000,
            "updated_at": "2025-01-01T00:00:00Z",
            "root_paths": ["README.md", "examples/pytorch", "src/transformers"],
            "readme_text": "Models, papers, examples, and documentation for the Transformers library.",
        },
    )

    explanation = score_provider_result(analysis, item)

    assert explanation.repo_role == "official_implementation"
    assert explanation.cap_reason != "paper_collection_cap"
    assert "discovery lead only; verify the actual implementation repo separately" not in explanation.reference_utility


def test_noncanonical_model_zoo_still_uses_model_zoo_cap() -> None:
    item = ProviderSearchResult(
        title="owner/checkpoint-zoo",
        url="https://github.com/owner/checkpoint-zoo",
        source="github",
        source_type="github",
        snippet="Model zoo and pretrained weights for vision models",
        metadata={
            "full_name": "owner/checkpoint-zoo",
            "owner": "owner",
            "stargazers_count": 10000,
            "updated_at": "2025-01-01T00:00:00Z",
            "root_paths": ["README.md", "requirements.txt", "configs/default.yaml", "weights/model.pth"],
            "readme_text": "Model zoo with checkpoint and pretrained weights only.",
        },
    )

    explanation = score_provider_result(analyze_query("paper code pytorch"), item)

    assert explanation.repo_role == "model_zoo"
    assert explanation.cap_reason == "model_zoo_cap"
    assert explanation.score <= 0.76
