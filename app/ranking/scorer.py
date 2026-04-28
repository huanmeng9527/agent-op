from __future__ import annotations

import math
import re
from datetime import UTC, datetime
from typing import Any

from app.core.query_analyzer import TECH_TERMS
from app.core.retrieval_profiles import build_repo_aliases
from app.ranking.types import ScoreExplanation
from app.schemas import ProviderSearchResult, QueryAnalysis
from app.utils.text import contains_term, safe_lower, unique_preserve_order, words_from_identifier


REPRO_ASSET_PATH_HINTS = {
    "has_training_code": ["train.py", "trainer.py", "fit.py", "main_train.py", "scripts/train.py", "tools/train.py", "train"],
    "has_eval_code": ["eval.py", "evaluate.py", "evaluation.py", "benchmark.py", "scripts/eval.py", "tools/eval.py", "eval", "evaluation", "benchmarks"],
    "has_config": ["config.py", "config", "configs", "conf", ".yaml", ".yml", "hydra"],
    "has_requirements": ["requirements.txt", "environment.yml", "environment.yaml", "pyproject.toml", "setup.py", "dockerfile", "docker"],
    "has_dataset_doc": ["dataset", "datasets", "data", "download.py", "prepare_data.py"],
    "has_checkpoint_hint": ["checkpoint", "checkpoints", "pretrained", "weights", "model_zoo", "ckpt"],
    "has_notebook": [".ipynb", "notebooks", "notebook"],
    "has_results": ["results", "benchmark", "benchmarks", "metrics", "leaderboard"],
}

REPRO_ASSET_TEXT_HINTS = {
    "has_training_code": ["train the model", "training script", "run training", "训练"],
    "has_eval_code": ["run evaluation", "evaluation script", "evaluate the model", "评估"],
    "has_config": ["configuration", "config file", "yaml", "hydra"],
    "has_requirements": ["requirements.txt", "environment.yml", "conda environment", "docker", "install dependencies"],
    "has_dataset_doc": ["dataset", "download data", "prepare data", "数据集"],
    "has_checkpoint_hint": ["checkpoint", "pretrained weights", "model zoo", "ckpt", "预训练"],
    "has_notebook": ["notebook", "colab"],
    "has_results": ["results", "benchmark", "metrics", "leaderboard"],
}

OFFICIAL_HINTS = ["official", "official implementation", "official code", "official repository", "code for our paper", "source code for our paper"]
UNOFFICIAL_HINTS = ["unofficial", "reimplementation", "reproduction", "复现"]
LOW_VALUE_HINTS = ["awesome", "reading list", "survey", "papers", "notes only"]
RISK_HINTS = ["homework", "assignment", "course project", "solution", "答案", "作业"]
MODEL_ZOO_HINTS = ["model zoo", "pretrained weights", "checkpoint", "checkpoints", "weights"]
DEMO_ONLY_HINTS = ["demo", "inference", "gradio", "streamlit", "web demo"]
RESEARCH_ORG_HINTS = [
    "facebookresearch",
    "google-research",
    "google-deepmind",
    "deepmind",
    "openai",
    "microsoft",
    "nvlabs",
    "nvidia",
    "salesforce",
    "huggingface",
    "allenai",
    "open-mmlab",
    "mlfoundations",
    "compvis",
    "paddlepaddle",
]

SCORE_CAPS = {
    "archived_cap": 0.60,
    "high_risk_cap": 0.62,
    "paper_collection_cap": 0.68,
    "weak_assets_cap": 0.70,
    "demo_only_cap": 0.72,
    "model_zoo_cap": 0.76,
    "incomplete_execution_cap": 0.84,
}


def _joined_text(item: ProviderSearchResult) -> str:
    metadata = item.metadata or {}
    parts = [
        item.title,
        words_from_identifier(item.title),
        item.snippet,
        str(metadata.get("description") or ""),
        str(metadata.get("readme_text") or ""),
        str(metadata.get("owner") or ""),
        " ".join(metadata.get("topics") or []),
        " ".join(metadata.get("root_paths") or []),
    ]
    return " ".join(part for part in parts if part)


def infer_tech_stack(text: str) -> list[str]:
    hits = [term for term in TECH_TERMS if contains_term(text, term)]
    if contains_term(text, "torch") and "pytorch" not in hits:
        hits.append("pytorch")
    if contains_term(text, "tf") and "tensorflow" not in hits:
        hits.append("tensorflow")
    return unique_preserve_order(hits)


def _path_matches(path: str, hint: str) -> bool:
    normalized_path = safe_lower(path).replace("\\", "/").strip("/")
    normalized_hint = safe_lower(hint).strip("/")
    if not normalized_path or not normalized_hint:
        return False
    if normalized_hint.startswith("."):
        return normalized_path.endswith(normalized_hint)
    if "/" in normalized_hint or "." in normalized_hint or "_" in normalized_hint:
        padded_path = f"/{normalized_path}/"
        return (
            normalized_path == normalized_hint
            or normalized_path.endswith(f"/{normalized_hint}")
            or f"/{normalized_hint}/" in padded_path
        )
    return normalized_hint in normalized_path.split("/")


def _matches_any_text_hint(text: str, hints: list[str]) -> bool:
    return any(contains_term(text, hint) for hint in hints)


def detect_reproduction_assets(metadata: dict[str, Any], readme_text: str = "") -> dict[str, bool]:
    root_paths = [
        safe_lower(path)
        for path in [*(metadata.get("root_paths") or []), *(metadata.get("tree_paths") or [])]
    ]
    combined_readme = " ".join([str(metadata.get("readme_text") or ""), readme_text])
    return {
        key: (
            any(_path_matches(path, hint) for path in root_paths for hint in REPRO_ASSET_PATH_HINTS[key])
            or _matches_any_text_hint(combined_readme, REPRO_ASSET_TEXT_HINTS[key])
        )
        for key in REPRO_ASSET_PATH_HINTS
    }


def classify_repo_role(text: str, assets: dict[str, bool]) -> str:
    if any(contains_term(text, hint) for hint in LOW_VALUE_HINTS):
        return "paper_collection"
    if any(contains_term(text, hint) for hint in UNOFFICIAL_HINTS):
        return "reproduction"
    if any(contains_term(text, hint) for hint in OFFICIAL_HINTS):
        return "official_implementation"
    if any(contains_term(text, hint) for hint in RESEARCH_ORG_HINTS):
        return "official_implementation"
    if any(contains_term(text, hint) for hint in MODEL_ZOO_HINTS) and not (
        assets.get("has_training_code") or assets.get("has_eval_code")
    ):
        return "model_zoo"
    if any(contains_term(text, hint) for hint in DEMO_ONLY_HINTS) and not assets.get("has_training_code"):
        return "demo_only"
    if assets.get("has_training_code") or assets.get("has_eval_code"):
        return "implementation"
    return "unknown"


def _freshness_score(updated_at: str | None) -> float:
    if not updated_at:
        return 0.45
    try:
        parsed = datetime.fromisoformat(updated_at.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return 0.45
    days = max(0, (datetime.now(UTC) - parsed).days)
    if days <= 365:
        return 1.0
    if days <= 365 * 3:
        return 0.75
    return 0.45


def _popularity_score(stars: int | None) -> float:
    if not stars:
        return 0.35
    return min(1.0, math.log10(stars + 1) / 4)


def _query_match_score(analysis: QueryAnalysis, text: str) -> tuple[float, list[str]]:
    evidence: list[str] = []
    score = 0.35
    if analysis.paper_title and contains_term(text, analysis.paper_title):
        score += 0.30
        evidence.append("repository text mentions the requested paper title")
    if analysis.task and contains_term(text, analysis.task.replace("_", " ")):
        score += 0.12
        evidence.append(f"repository text matches task: {analysis.task}")
    for keyword in analysis.tech_keywords[:3]:
        if contains_term(text, keyword):
            score += 0.05
            evidence.append(f"matches requested tech keyword: {keyword}")
    if analysis.year and contains_term(text, str(analysis.year)):
        score += 0.06
        evidence.append(f"mentions target year {analysis.year}")
    if analysis.venue and contains_term(text, analysis.venue):
        score += 0.06
        evidence.append(f"mentions venue {analysis.venue}")
    return min(1.0, score), evidence


def _normalize_identity(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", safe_lower(value)).strip()


def _repo_name_identity_bonus(analysis: QueryAnalysis, metadata: dict[str, Any], title: str) -> tuple[float, list[str]]:
    if not analysis.paper_title:
        return 0.0, []
    full_name = str(metadata.get("full_name") or title or "")
    repo_name = full_name.rsplit("/", 1)[-1] if "/" in full_name else full_name
    normalized_repo = _normalize_identity(repo_name)
    normalized_title = _normalize_identity(analysis.paper_title)
    if not normalized_repo or not normalized_title:
        return 0.0, []
    compact_repo = normalized_repo.replace(" ", "")
    compact_title = normalized_title.replace(" ", "")
    if normalized_repo == normalized_title or compact_repo == compact_title:
        return 0.25, ["repository name exactly matches the requested paper title"]
    title_tokens = normalized_title.split()
    repo_tokens = normalized_repo.split()
    if all(token in repo_tokens for token in title_tokens):
        return 0.10, ["repository name contains all requested paper-title tokens"]
    if compact_title and compact_title in compact_repo:
        return 0.06, ["repository name partially matches the requested paper title"]
    return 0.0, []


def _canonical_research_org_bonus(analysis: QueryAnalysis, metadata: dict[str, Any], title: str) -> tuple[float, list[str]]:
    match = _canonical_research_org_match(analysis, metadata, title)
    if match == "exact":
        return 0.12, ["canonical research-org repository exactly matches a short paper alias"]
    if match == "near":
        return 0.03, ["canonical research-org repository nearly matches a short paper alias"]
    return 0.0, []


def _canonical_research_org_match(analysis: QueryAnalysis, metadata: dict[str, Any], title: str) -> str | None:
    owner = safe_lower(str(metadata.get("owner") or ""))
    if owner not in RESEARCH_ORG_HINTS:
        return None
    full_name = str(metadata.get("full_name") or title or "")
    repo_name = _normalize_identity(full_name.rsplit("/", 1)[-1] if "/" in full_name else full_name)
    if not repo_name:
        return None
    repo_compact = repo_name.replace(" ", "")
    near_match = False
    for alias in build_repo_aliases(analysis):
        normalized_alias = _normalize_identity(alias)
        alias_compact = normalized_alias.replace(" ", "")
        if alias_compact and repo_compact == alias_compact:
            return "exact"
        if alias_compact and repo_compact.startswith(alias_compact):
            near_match = True
    if near_match:
        return "near"
    return None


def _asset_score(assets: dict[str, bool]) -> tuple[float, list[str]]:
    weights = {
        "has_training_code": 0.20,
        "has_eval_code": 0.16,
        "has_config": 0.10,
        "has_requirements": 0.12,
        "has_dataset_doc": 0.12,
        "has_checkpoint_hint": 0.10,
        "has_results": 0.10,
        "has_notebook": 0.05,
    }
    score = 0.20 + sum(weight for key, weight in weights.items() if assets.get(key))
    evidence = [key.replace("_", " ") for key in weights if assets.get(key)]
    return min(1.0, score), evidence


def _risk_level(text: str, repo_role: str, assets: dict[str, bool]) -> tuple[str, list[str]]:
    negative: list[str] = []
    if any(contains_term(text, hint) for hint in RISK_HINTS):
        negative.append("contains homework/solution-like wording")
        return "high", negative
    if repo_role == "paper_collection":
        negative.append("looks like a paper list rather than runnable reproduction code")
        return "medium", negative
    if repo_role == "demo_only":
        negative.append("looks demo/inference-oriented; training path is not detected")
    if repo_role == "model_zoo":
        negative.append("looks checkpoint/model-zoo-oriented; runnable reproduction assets are incomplete")
    if not assets.get("has_requirements"):
        negative.append("dependency or environment file not detected")
    if not assets.get("has_eval_code"):
        negative.append("evaluation script not detected")
    return ("medium" if negative else "low"), negative[:3]


def _score_cap(
    *,
    metadata: dict[str, Any],
    repo_role: str,
    assets: dict[str, bool],
    risk_level: str,
    protect_canonical_official: bool = False,
) -> tuple[float, str | None]:
    caps: list[tuple[str, float]] = []
    if metadata.get("archived") and not protect_canonical_official:
        caps.append(("archived_cap", SCORE_CAPS["archived_cap"]))
    if risk_level == "high":
        caps.append(("high_risk_cap", SCORE_CAPS["high_risk_cap"]))
    if repo_role == "paper_collection":
        caps.append(("paper_collection_cap", SCORE_CAPS["paper_collection_cap"]))
    if repo_role == "demo_only":
        caps.append(("demo_only_cap", SCORE_CAPS["demo_only_cap"]))
    if repo_role == "model_zoo":
        caps.append(("model_zoo_cap", SCORE_CAPS["model_zoo_cap"]))

    asset_count = sum(1 for value in assets.values() if value)
    if protect_canonical_official:
        pass
    elif asset_count <= 1:
        caps.append(("weak_assets_cap", SCORE_CAPS["weak_assets_cap"]))
    elif not (assets.get("has_training_code") and (assets.get("has_eval_code") or assets.get("has_results"))):
        caps.append(("incomplete_execution_cap", SCORE_CAPS["incomplete_execution_cap"]))

    if not caps:
        return 1.0, None
    cap_value = min(value for _, value in caps)
    for reason in (
        "archived_cap",
        "high_risk_cap",
        "paper_collection_cap",
        "weak_assets_cap",
        "demo_only_cap",
        "model_zoo_cap",
        "incomplete_execution_cap",
    ):
        if any(existing_reason == reason for existing_reason, _ in caps):
            return cap_value, reason
    return cap_value, caps[0][0]


def _reference_utility(repo_role: str, assets: dict[str, bool]) -> list[str]:
    utility: list[str] = []
    if assets.get("has_requirements"):
        utility.append("environment setup reference")
    if assets.get("has_training_code"):
        utility.append("training pipeline reference")
    if assets.get("has_eval_code") or assets.get("has_results"):
        utility.append("evaluation and metric reference")
    if assets.get("has_dataset_doc"):
        utility.append("dataset preparation reference")
    if assets.get("has_checkpoint_hint"):
        utility.append("checkpoint/pretrained model reference")
    if assets.get("has_config"):
        utility.append("experiment configuration reference")
    if repo_role == "official_implementation":
        utility.insert(0, "primary source for paper-author implementation claims")
    elif repo_role == "reproduction":
        utility.insert(0, "cross-check reference for independent reproduction attempts")
    elif repo_role == "paper_collection":
        utility.append("discovery lead only; verify the actual implementation repo separately")
    return unique_preserve_order(utility)[:5]


def _level(score: float) -> str:
    if score >= 0.76:
        return "high"
    if score >= 0.55:
        return "medium"
    return "low"


def score_provider_result(analysis: QueryAnalysis, item: ProviderSearchResult) -> ScoreExplanation:
    metadata = dict(item.metadata or {})
    text = _joined_text(item)
    assets = detect_reproduction_assets(metadata, str(metadata.get("readme_text") or ""))
    repo_role = classify_repo_role(text, assets)
    canonical_match = _canonical_research_org_match(analysis, metadata, item.title)
    if canonical_match == "exact" and repo_role in {"paper_collection", "reproduction", "unknown"}:
        repo_role = "official_implementation"
    tech_stack = infer_tech_stack(text)
    query_score, query_evidence = _query_match_score(analysis, text)
    identity_bonus, identity_evidence = _repo_name_identity_bonus(analysis, metadata, item.title)
    canonical_bonus, canonical_evidence = _canonical_research_org_bonus(analysis, metadata, item.title)
    query_score = min(1.0, query_score + identity_bonus)
    query_evidence = [*identity_evidence, *canonical_evidence, *query_evidence]
    asset_score, asset_evidence = _asset_score(assets)
    freshness = _freshness_score(metadata.get("updated_at"))
    popularity = _popularity_score(metadata.get("stargazers_count"))
    risk_level, negative = _risk_level(text, repo_role, assets)
    if metadata.get("archived"):
        negative.append("repository is archived")

    role_bonus = {
        "official_implementation": 0.10,
        "reproduction": 0.08,
        "implementation": 0.05,
        "model_zoo": 0.02,
        "demo_only": 0.01,
        "paper_collection": -0.10,
        "unknown": 0.0,
    }.get(repo_role, 0.0)
    role_bonus += canonical_bonus
    risk_penalty = {"low": 0.0, "medium": 0.06, "high": 0.20}[risk_level]
    raw_score = (
        query_score * 0.42
        + asset_score * 0.30
        + freshness * 0.08
        + popularity * 0.10
        + min(1.0, len(tech_stack) / 3) * 0.10
        + role_bonus
        - risk_penalty
    )
    protect_canonical_official = canonical_match == "exact" and repo_role == "official_implementation" and risk_level != "high"
    cap, cap_reason = _score_cap(
        metadata=metadata,
        repo_role=repo_role,
        assets=assets,
        risk_level=risk_level,
        protect_canonical_official=protect_canonical_official,
    )
    score = round(max(0.0, min(cap, raw_score)), 4)
    if protect_canonical_official and not cap_reason:
        score = max(score, 0.75)
    confidence = "high" if score >= 0.76 and len(asset_evidence) >= 4 and not cap_reason else _level(score)
    positive = unique_preserve_order([*query_evidence, *asset_evidence])
    if tech_stack:
        positive.append(f"detects tech stack: {', '.join(tech_stack[:5])}")
    if repo_role != "unknown":
        positive.append(f"classified as {repo_role}")
    if cap_reason:
        negative.append(f"score capped by {cap_reason}")
    why = "Strong reproduction candidate with runnable-code signals." if score >= 0.76 else (
        "Useful reproduction reference, but verify assets and experiment fidelity." if score >= 0.55 else
        "Weak candidate; treat as a discovery lead rather than a primary reproduction reference."
    )
    return ScoreExplanation(
        score=score,
        value_level=_level(score),
        confidence_level=confidence,
        risk_level=risk_level,
        repo_role=repo_role,
        cap_reason=cap_reason,
        tech_stack=tech_stack,
        reproduction_signals=asset_evidence,
        reference_utility=_reference_utility(repo_role, assets),
        positive_evidence=positive[:6],
        negative_evidence=unique_preserve_order(negative)[:4],
        why_recommended=why,
    )
