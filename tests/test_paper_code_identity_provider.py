import asyncio
import json

from app.core.query_analyzer import analyze_query
from app.core.service import PaperReproductionIntelligenceService
from app.providers.paper_code_identity import DEFAULT_OVERRIDES_PATH, PaperCodeIdentityProvider
from app.providers.registry import ProviderRegistry
from app.schemas import ProviderSearchResult, SearchPaperReposInput, SearchResultItem


class NullPaperMetadataProvider:
    async def resolve(self, query: str | None, *, paper_title: str | None = None):
        return None


class FakeGitHubProvider:
    name = "github"
    source_type = "github"
    capabilities = frozenset({"repository_search", "repository_inspection"})

    def __init__(self, search_results: list[ProviderSearchResult] | None = None) -> None:
        self.search_results = search_results or []
        self.identity_matches = []

    def supports(self, capability: str) -> bool:
        return capability in self.capabilities

    async def fetch_identity_candidates(self, matches):
        self.identity_matches = list(matches)
        return [
            ProviderSearchResult(
                title=match.repo,
                url=f"https://github.com/{match.repo}",
                source=self.name,
                source_type=self.source_type,
                snippet=f"External paper identity evidence: {match.evidence}; official code for {match.title}",
                metadata={
                    "full_name": match.repo,
                    "owner": match.repo.split("/", 1)[0],
                    "description": f"Official implementation for {match.title}",
                    "languages": ["Python"],
                    "stargazers_count": 10000,
                    "updated_at": "2025-01-01T00:00:00Z",
                    "root_paths": ["train.py", "eval.py", "requirements.txt", "configs/default.yaml"],
                    "external_identity": match.to_metadata(),
                    "external_identity_source": match.source,
                    "external_identity_confidence": match.confidence,
                    "external_identity_evidence": match.evidence,
                },
            )
            for match in matches
        ]

    async def search(self, analysis, *, top_k: int = 5):
        return self.search_results[:top_k]


def _write_overrides(tmp_path, entries):
    path = tmp_path / "paper_code_identity_overrides.json"
    path.write_text(json.dumps(entries), encoding="utf-8")
    return path


def test_identity_provider_resolves_by_title_arxiv_and_case_id(tmp_path) -> None:
    overrides_path = _write_overrides(
        tmp_path,
        [
            {
                "paper_id": "case_1",
                "title": "A Very Specific Paper Title",
                "arxiv_id": "2401.01234",
                "official_repos": ["example/specific-paper"],
                "source": "curated_override",
                "confidence": "high",
                "note": "Test mapping.",
            }
        ],
    )
    provider = PaperCodeIdentityProvider(overrides_path)

    by_title = provider.resolve(analyze_query("Specific Paper Title paper code", paper_title="A Very Specific Paper Title"))
    by_arxiv = provider.resolve(analyze_query("unrelated query"), arxiv_id="2401.01234")
    by_case = provider.resolve(analyze_query("unrelated query"), paper_id="case_1")

    assert [match.repo for match in by_title] == ["example/specific-paper"]
    assert [match.repo for match in by_arxiv] == ["example/specific-paper"]
    assert [match.repo for match in by_case] == ["example/specific-paper"]
    assert by_title[0].source == "curated_override"
    assert by_title[0].confidence == "high"
    assert by_title[0].identity_type == "official"
    assert "A Very Specific Paper Title" in by_title[0].evidence


def test_search_flow_injects_identity_repo_with_evidence(tmp_path) -> None:
    overrides_path = _write_overrides(
        tmp_path,
        [
            {
                "paper_id": "llava_2023",
                "title": "Visual Instruction Tuning",
                "official_repos": ["haotian-liu/LLaVA"],
                "source": "curated_override",
                "confidence": "high",
                "note": "Repo branding differs from the paper title.",
            }
        ],
    )
    fake_github = FakeGitHubProvider()
    service = PaperReproductionIntelligenceService(
        registry=ProviderRegistry(providers=[fake_github]),
        paper_metadata_provider=NullPaperMetadataProvider(),
        paper_code_identity_provider=PaperCodeIdentityProvider(overrides_path),
    )

    result = asyncio.run(
        service.search_paper_repos(
            SearchPaperReposInput(
                query="LLaVA Visual Instruction Tuning paper code",
                paper_title="Visual Instruction Tuning",
                top_k=3,
            )
        )
    )

    assert [match.repo for match in fake_github.identity_matches] == ["haotian-liu/LLaVA"]
    assert result.results[0].repo == "haotian-liu/LLaVA"
    assert result.results[0].identity_source == "curated_override"
    assert result.results[0].identity_confidence == "high"
    assert result.results[0].identity_type == "official"
    assert "Visual Instruction Tuning" in result.results[0].identity_evidence[0]
    assert result.provider_status["paper_code_identity"]["matched_repos"] == ["haotian-liu/LLaVA"]
    assert result.provider_status["paper_code_identity"]["matched_identity_types"] == ["official"]


def test_search_flow_injects_non_official_reproduction_identity(tmp_path) -> None:
    overrides_path = _write_overrides(
        tmp_path,
        [
            {
                "paper_id": "deepfm_2017",
                "title": "DeepFM: A Factorization-Machine based Neural Network for CTR Prediction",
                "identity_type": "domain_library_implementation",
                "target_repos": ["shenweichen/DeepCTR"],
                "source": "curated_override",
                "confidence": "medium-high",
                "evidence": "DeepCTR includes DeepFM / CTR model implementations.",
            }
        ],
    )
    fake_github = FakeGitHubProvider()
    service = PaperReproductionIntelligenceService(
        registry=ProviderRegistry(providers=[fake_github]),
        paper_metadata_provider=NullPaperMetadataProvider(),
        paper_code_identity_provider=PaperCodeIdentityProvider(overrides_path),
    )

    result = asyncio.run(
        service.search_paper_repos(
            SearchPaperReposInput(
                query="DeepFM Factorization-Machine Neural Network CTR Prediction code",
                paper_title="DeepFM: A Factorization-Machine based Neural Network for CTR Prediction",
                top_k=3,
            )
        )
    )

    assert [match.repo for match in fake_github.identity_matches] == ["shenweichen/DeepCTR"]
    assert fake_github.identity_matches[0].identity_type == "domain_library_implementation"
    assert result.results[0].repo == "shenweichen/DeepCTR"
    assert result.results[0].identity_type == "domain_library_implementation"
    assert result.results[0].identity_confidence == "medium-high"
    assert result.provider_status["paper_code_identity"]["matched_identity_types"] == [
        "domain_library_implementation"
    ]


def test_search_flow_without_mapping_keeps_regular_results(tmp_path) -> None:
    overrides_path = _write_overrides(tmp_path, [])
    regular_result = ProviderSearchResult(
        title="example/regular",
        url="https://github.com/example/regular",
        source="github",
        source_type="github",
        snippet="Regular GitHub search result with train.py and eval.py",
        metadata={
            "full_name": "example/regular",
            "owner": "example",
            "languages": ["Python"],
            "stargazers_count": 10,
            "updated_at": "2025-01-01T00:00:00Z",
            "root_paths": ["train.py", "eval.py", "requirements.txt"],
        },
    )
    fake_github = FakeGitHubProvider(search_results=[regular_result])
    service = PaperReproductionIntelligenceService(
        registry=ProviderRegistry(providers=[fake_github]),
        paper_metadata_provider=NullPaperMetadataProvider(),
        paper_code_identity_provider=PaperCodeIdentityProvider(overrides_path),
    )

    result = asyncio.run(
        service.search_paper_repos(
            SearchPaperReposInput(
                query="Some unmapped paper code",
                paper_title="Some Unmapped Paper",
                top_k=3,
            )
        )
    )

    assert fake_github.identity_matches == []
    assert [item.repo for item in result.results] == ["example/regular"]
    assert result.results[0].identity_source is None
    assert result.provider_status["paper_code_identity"]["result_count"] == 0


def test_high_confidence_identity_candidate_is_retained_at_top_k_boundary() -> None:
    service = PaperReproductionIntelligenceService()
    regular_results = [
        SearchResultItem(
            title=f"example/repo-{index}",
            url=f"https://github.com/example/repo-{index}",
            repo=f"example/repo-{index}",
            source="github",
            source_type="github",
            score=0.9 - index * 0.1,
        )
        for index in range(4)
    ]
    identity_result = SearchResultItem(
        title="official/project",
        url="https://github.com/official/project",
        repo="official/project",
        source="github",
        source_type="github",
        score=0.2,
        identity_source="curated_override",
        identity_confidence="high",
        identity_evidence=["curated identity maps the paper to this repo"],
    )

    retained = service._retain_high_confidence_identity_candidates(
        [*regular_results, identity_result],
        top_k=3,
    )

    assert retained[0].repo == "example/repo-0"
    assert [item.repo for item in retained[:3]] == ["example/repo-0", "example/repo-1", "official/project"]


def test_curated_identity_round2_targets_have_evidence_and_resolve() -> None:
    expected = {
        "t5_2019": (
            "Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer",
            ["google-research/text-to-text-transfer-transformer"],
        ),
        "guided_diffusion_2021": (
            "Diffusion Models Beat GANs on Image Synthesis",
            ["openai/guided-diffusion"],
        ),
        "midas_2020": (
            "Towards Robust Monocular Depth Estimation: Mixing Datasets for Zero-shot Cross-dataset Transfer",
            ["isl-org/MiDaS"],
        ),
        "wav2vec2_2020": (
            "wav2vec 2.0: A Framework for Self-Supervised Learning of Speech Representations",
            ["facebookresearch/fairseq"],
        ),
        "hubert_2021": (
            "HuBERT: Self-Supervised Speech Representation Learning by Masked Prediction of Hidden Units",
            ["facebookresearch/fairseq"],
        ),
    }
    raw_entries = {
        entry["paper_id"]: entry
        for entry in json.loads(DEFAULT_OVERRIDES_PATH.read_text(encoding="utf-8"))
    }
    provider = PaperCodeIdentityProvider(DEFAULT_OVERRIDES_PATH)

    for paper_id, (title, repos) in expected.items():
        entry = raw_entries[paper_id]
        matches = provider.resolve(analyze_query(f"{title} paper code", paper_title=title))

        assert entry["official_repos"] == repos
        assert entry["source"] == "curated_override"
        assert entry["confidence"] == "high"
        assert entry["evidence"]
        assert [match.repo for match in matches] == repos
        assert matches[0].confidence == "high"
        assert "Source:" in matches[0].evidence


def test_curated_identity_round3_targets_have_evidence_and_resolve() -> None:
    expected = {
        "vit_2020": (
            "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale",
            "Vision Transformer An Image is Worth 16x16 Words paper code",
            ["google-research/vision_transformer"],
            "high",
        ),
        "colmap_2016": (
            "Structure-from-Motion Revisited",
            "COLMAP Structure-from-Motion Revisited paper code",
            ["colmap/colmap"],
            "high",
        ),
        "lightgcn_2020": (
            "LightGCN: Simplifying and Powering Graph Convolution Network for Recommendation",
            "LightGCN Simplifying and Powering Graph Convolution Network for Recommendation code",
            ["gusye1234/LightGCN-PyTorch"],
            "high",
        ),
        "ultralytics_yolov8_2023": (
            "YOLOv8",
            "YOLOv8 object detection segmentation pose paper code",
            ["ultralytics/ultralytics"],
            "high",
        ),
        "yolov7_2022": (
            "YOLOv7: Trainable bag-of-freebies sets new state-of-the-art for real-time object detectors",
            "YOLOv7 Trainable bag-of-freebies real-time object detectors code",
            ["WongKinYiu/yolov7"],
            "high",
        ),
        "deepspeech2_2015": (
            "Deep Speech 2: End-to-End Speech Recognition in English and Mandarin",
            "Deep Speech 2 End-to-End Speech Recognition English Mandarin code",
            ["PaddlePaddle/DeepSpeech"],
            "high",
        ),
    }
    raw_entries = {
        entry["paper_id"]: entry
        for entry in json.loads(DEFAULT_OVERRIDES_PATH.read_text(encoding="utf-8"))
    }
    provider = PaperCodeIdentityProvider(DEFAULT_OVERRIDES_PATH)

    for paper_id, (title, query, repos, confidence) in expected.items():
        entry = raw_entries[paper_id]
        matches = provider.resolve(analyze_query(query, paper_title=title))

        assert entry["official_repos"] == repos
        assert entry.get("identity_type", "official") == "official"
        assert entry["source"] == "curated_override"
        assert entry["confidence"] == confidence
        assert entry["evidence"]
        assert [match.repo for match in matches] == repos
        assert matches[0].identity_type == "official"
        assert matches[0].confidence == confidence
        assert "Source:" in matches[0].evidence


def test_dino_style_identity_overlap_does_not_match_vision_transformer() -> None:
    provider = PaperCodeIdentityProvider(DEFAULT_OVERRIDES_PATH)
    matches = provider.resolve(
        analyze_query(
            "DINO Emerging Properties in Self-Supervised Vision Transformers paper code pytorch ICCV 2021",
            paper_title="Emerging Properties in Self-Supervised Vision Transformers",
        )
    )

    assert "google-research/vision_transformer" not in [match.repo.casefold() for match in matches]


def test_identity_guard_keeps_vit_exact_title_match() -> None:
    provider = PaperCodeIdentityProvider(DEFAULT_OVERRIDES_PATH)
    matches = provider.resolve(
        analyze_query(
            "Vision Transformer An Image is Worth 16x16 Words paper code",
            paper_title="An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale",
        )
    )

    assert [match.repo for match in matches] == ["google-research/vision_transformer"]


def test_identity_guard_keeps_stable_diffusion_t5_and_reproduction_mappings() -> None:
    provider = PaperCodeIdentityProvider(DEFAULT_OVERRIDES_PATH)
    checks = [
        (
            "High-Resolution Image Synthesis with Latent Diffusion Models paper code",
            "High-Resolution Image Synthesis with Latent Diffusion Models",
            ["CompVis/latent-diffusion", "CompVis/stable-diffusion"],
        ),
        (
            "Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer code",
            "Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer",
            ["google-research/text-to-text-transfer-transformer"],
        ),
        (
            "Collaborative Filtering for Implicit Feedback Datasets paper code",
            "Collaborative Filtering for Implicit Feedback Datasets",
            ["benfred/implicit"],
        ),
        (
            "DeepFM Factorization-Machine Neural Network CTR Prediction code",
            "DeepFM: A Factorization-Machine based Neural Network for CTR Prediction",
            ["shenweichen/DeepCTR"],
        ),
    ]

    for query, title, repos in checks:
        matches = provider.resolve(analyze_query(query, paper_title=title))
        assert [match.repo for match in matches] == repos


def test_exact_normalized_title_matches_without_case_id_or_arxiv(tmp_path) -> None:
    overrides_path = _write_overrides(
        tmp_path,
        [
            {
                "paper_id": "case_1",
                "title": "Exact Normalized Title",
                "official_repos": ["example/exact-title"],
                "source": "curated_override",
                "confidence": "high",
            }
        ],
    )
    provider = PaperCodeIdentityProvider(overrides_path)

    matches = provider.resolve(analyze_query("unrelated lookup", paper_title="Exact Normalized Title"))

    assert [match.repo for match in matches] == ["example/exact-title"]


def test_generic_token_overlap_alone_does_not_match_identity(tmp_path) -> None:
    overrides_path = _write_overrides(
        tmp_path,
        [
            {
                "paper_id": "vision_transformer_case",
                "title": "Vision Transformer",
                "official_repos": ["example/vision-transformer"],
                "source": "curated_override",
                "confidence": "high",
            }
        ],
    )
    provider = PaperCodeIdentityProvider(overrides_path)

    matches = provider.resolve(
        analyze_query(
            "Emerging Properties in Self-Supervised Vision Transformers paper code",
            paper_title="Emerging Properties in Self-Supervised Vision Transformers",
        )
    )

    assert matches == []


def test_curated_reproduction_identity_targets_have_evidence_and_resolve() -> None:
    expected = {
        "implicit_mf_2008": (
            "Collaborative Filtering for Implicit Feedback Datasets",
            "Collaborative Filtering for Implicit Feedback Datasets paper code",
            ["benfred/implicit"],
            "medium",
        ),
        "deepfm_2017": (
            "DeepFM: A Factorization-Machine based Neural Network for CTR Prediction",
            "DeepFM Factorization-Machine Neural Network CTR Prediction code",
            ["shenweichen/DeepCTR"],
            "medium-high",
        ),
    }
    raw_entries = {
        entry["paper_id"]: entry
        for entry in json.loads(DEFAULT_OVERRIDES_PATH.read_text(encoding="utf-8"))
    }
    provider = PaperCodeIdentityProvider(DEFAULT_OVERRIDES_PATH)

    for paper_id, (title, query, repos, confidence) in expected.items():
        entry = raw_entries[paper_id]
        matches = provider.resolve(analyze_query(query, paper_title=title))

        assert "official_repos" not in entry
        assert entry["target_repos"] == repos
        assert entry["identity_type"] == "domain_library_implementation"
        assert entry["source"] == "curated_override"
        assert entry["confidence"] == confidence
        assert entry["evidence"]
        assert [match.repo for match in matches] == repos
        assert matches[0].identity_type == "domain_library_implementation"
        assert matches[0].confidence == confidence
        assert "Source:" in matches[0].evidence
