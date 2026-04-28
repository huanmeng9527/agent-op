from app.core.query_analyzer import analyze_query
from app.core.retrieval_profiles import build_repo_aliases
from app.providers.github import GitHubProvider


def test_search_queries_do_not_force_pytorch_when_not_requested() -> None:
    analysis = analyze_query("Graph Attention Networks tensorflow implementation")
    queries = GitHubProvider()._build_search_queries(analysis)

    assert all("pytorch" not in query.casefold() for query in queries)
    assert any("tensorflow" in query.casefold() for query in queries)
    assert all("archived:false" in query for query in queries)


def test_search_queries_expand_exact_paper_title_for_reproduction() -> None:
    analysis = analyze_query("Segment Anything CVPR 2023 pytorch", paper_title="Segment Anything")
    queries = GitHubProvider()._build_search_queries(analysis)
    combined = "\n".join(queries).casefold()

    assert '"segment anything" "official implementation"' in combined
    assert '"segment anything" reproduction' in combined
    assert "cvpr" in combined


def test_search_queries_frontload_short_aliases() -> None:
    analysis = analyze_query(
        "DETR End-to-End Object Detection with Transformers paper code pytorch ECCV 2020",
        paper_title="End-to-End Object Detection with Transformers",
    )
    queries = GitHubProvider()._build_search_queries(analysis)
    combined = "\n".join(queries[:4]).casefold()

    assert "detr in:name" in combined
    assert 'detr "official code"' in combined


def test_canonical_repo_pairs_use_research_org_alias_pattern() -> None:
    analysis = analyze_query(
        "Masked Autoencoders Are Scalable Vision Learners paper code pytorch",
        paper_title="Masked Autoencoders Are Scalable Vision Learners",
    )
    pairs = GitHubProvider()._canonical_repo_pairs(analysis)

    assert ("facebookresearch", "mae") in pairs


def test_versioned_paper_alias_precedes_broader_phrase_alias() -> None:
    analysis = analyze_query(
        "SAM 2 Segment Anything in Images and Videos paper code",
        paper_title="SAM 2: Segment Anything in Images and Videos",
    )
    aliases = build_repo_aliases(analysis)
    pairs = GitHubProvider()._canonical_repo_pairs(analysis)

    assert aliases[0] == "sam2"
    assert aliases.index("sam2") < aliases.index("segment-anything")
    assert pairs[0] == ("facebookresearch", "sam2")


def test_project_aliases_cover_title_and_query_prefixes() -> None:
    whisper = analyze_query(
        "Whisper Robust Speech Recognition via Large-Scale Weak Supervision paper code",
        paper_title="Robust Speech Recognition via Large-Scale Weak Supervision",
    )
    openclip = analyze_query(
        "Reproducible scaling laws for contrastive language-image learning OpenCLIP code",
        paper_title="Reproducible scaling laws for contrastive language-image learning",
    )

    assert "whisper" in build_repo_aliases(whisper)
    assert "open_clip" in build_repo_aliases(openclip)


def test_canonical_repo_pairs_include_extended_research_orgs() -> None:
    analysis = analyze_query(
        "Reproducible scaling laws for contrastive language-image learning OpenCLIP code",
        paper_title="Reproducible scaling laws for contrastive language-image learning",
    )
    pairs = GitHubProvider()._canonical_repo_pairs(analysis)

    assert ("mlfoundations", "open_clip") in pairs
