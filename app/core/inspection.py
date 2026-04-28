from __future__ import annotations

import re
from typing import Any

from app.ranking.scorer import detect_reproduction_assets
from app.utils.text import contains_term, safe_lower, truncate_text, unique_preserve_order


TRAINING_ENTRY_HINTS = ["train.py", "trainer.py", "main_train.py", "tools/train.py", "scripts/train.py", "train"]
EVAL_ENTRY_HINTS = ["eval.py", "evaluate.py", "evaluation.py", "test.py", "benchmark.py", "tools/eval.py", "scripts/eval.py"]
CONFIG_HINTS = [".yaml", ".yml", "config.py", "configs", "hydra", ".toml"]
ENV_LOCK_HINTS = [
    "conda-lock.yml",
    "poetry.lock",
    "uv.lock",
    "pdm.lock",
    "requirements.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
]
ENV_HINTS = ["requirements.txt", "environment.yml", "environment.yaml", "pyproject.toml", "setup.py", "dockerfile", "docker"]
DATASET_NAMES = [
    "coco",
    "imagenet",
    "cityscapes",
    "ade20k",
    "voc",
    "kinetics",
    "libri",
    "librispeech",
    "wikitext",
    "squad",
    "glue",
    "mnist",
    "cifar",
]
REPRODUCTION_TERMS = [
    "reproduce",
    "reproduction",
    "training",
    "evaluation",
    "prepare data",
    "download data",
    "run the following",
    "复现",
    "训练",
    "评估",
]


def _paths(metadata: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for key in ("tree_paths", "root_paths"):
        for path in metadata.get(key) or []:
            if path:
                paths.append(str(path))
    return unique_preserve_order(paths)


def _path_matches(path: str, hints: list[str]) -> bool:
    lowered = safe_lower(path).replace("\\", "/").strip("/")
    basename = lowered.rsplit("/", 1)[-1]
    for hint in hints:
        normalized = safe_lower(hint).strip("/")
        if normalized.startswith(".") and lowered.endswith(normalized):
            return True
        if "/" in normalized:
            if lowered == normalized or lowered.endswith(f"/{normalized}"):
                return True
        if basename == normalized or normalized in lowered.split("/"):
            return True
    return False


def _checkpoint_links(text: str) -> list[str]:
    urls = [url.rstrip(".,;:") for url in re.findall(r"https?://[^\s)\]>\"']+", text or "")]
    return [
        url
        for url in urls
        if any(contains_term(url, term) for term in ["checkpoint", "ckpt", "weights", "pretrained", "model"])
    ][:8]


def _arxiv_ids(text: str) -> list[str]:
    ids = re.findall(r"arxiv(?:\.org/(?:abs|pdf)/|:)\s*([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?)", text or "", flags=re.I)
    ids.extend(re.findall(r"\b([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?)\b", text or ""))
    return unique_preserve_order(ids)[:5]


def _doi_values(text: str) -> list[str]:
    return unique_preserve_order(re.findall(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", text or "", flags=re.I))[:5]


def _bibtex_entries(text: str) -> list[str]:
    matches = re.findall(r"@(article|inproceedings|misc|conference|proceedings)\s*\{[^,]{1,120}", text or "", flags=re.I)
    return unique_preserve_order([match.casefold() for match in matches])[:5]


def _config_dataset_refs(config_texts: dict[str, str], readme_text: str) -> list[str]:
    refs: list[str] = []
    combined_sources = {**config_texts, "README": readme_text}
    for source, text in combined_sources.items():
        lowered = safe_lower(text)
        if any(key in lowered for key in ("dataset", "data_root", "data_path", "datadir", "train_data")):
            refs.append(f"{source}: dataset/data path key")
        for dataset in DATASET_NAMES:
            if contains_term(text, dataset):
                refs.append(f"{source}: {dataset}")
    return unique_preserve_order(refs)[:8]


def _instruction_evidence(text: str) -> list[str]:
    return [term for term in REPRODUCTION_TERMS if contains_term(text, term)][:6]


def _judgement(level: str, reason: str, evidence: list[str]) -> dict[str, Any]:
    return {
        "level": level,
        "reason": reason,
        "evidence": unique_preserve_order([item for item in evidence if item])[:6],
    }


def _training_readiness(
    training_entries: list[str],
    config_dataset_refs: list[str],
    instruction_hits: list[str],
    assets: dict[str, bool],
) -> dict[str, Any]:
    evidence = [
        *training_entries[:3],
        *config_dataset_refs[:2],
        *[f"README/instructions mention `{term}`" for term in instruction_hits[:2]],
    ]
    if training_entries and (config_dataset_refs or instruction_hits):
        return _judgement(
            "ready",
            "Training entry points are present and tied to dataset/config or run instructions.",
            evidence,
        )
    if training_entries or assets.get("has_training_code"):
        return _judgement(
            "partial",
            "Training code is visible, but dataset/config/run evidence is incomplete.",
            evidence or training_entries,
        )
    return _judgement("missing", "No reliable training entry point was detected.", evidence)


def _evaluation_readiness(
    evaluation_entries: list[str],
    config_dataset_refs: list[str],
    instruction_hits: list[str],
    assets: dict[str, bool],
) -> dict[str, Any]:
    evidence = [
        *evaluation_entries[:3],
        *config_dataset_refs[:2],
        *[f"README/instructions mention `{term}`" for term in instruction_hits[:2]],
    ]
    if evaluation_entries and (assets.get("has_results") or config_dataset_refs or instruction_hits):
        return _judgement(
            "ready",
            "Evaluation entry points are present with metric/result, dataset, or run-instruction evidence.",
            evidence,
        )
    if evaluation_entries or assets.get("has_eval_code") or assets.get("has_results"):
        return _judgement(
            "partial",
            "Evaluation or result evidence exists, but the runnable evaluation path is incomplete.",
            evidence or evaluation_entries,
        )
    return _judgement("missing", "No reliable evaluation entry point was detected.", evidence)


def _environment_reproducibility(
    environment_files: list[str],
    lockfiles: list[str],
    assets: dict[str, bool],
) -> dict[str, Any]:
    if lockfiles:
        return _judgement(
            "locked",
            "Dependency lockfile or package lock is present.",
            [*lockfiles[:3], *environment_files[:3]],
        )
    if environment_files or assets.get("has_requirements"):
        return _judgement(
            "documented",
            "Environment files are present, but dependencies are not fully pinned.",
            environment_files[:6],
        )
    return _judgement("missing", "No dependency or environment file was detected.", [])


def _paper_identity_confidence(paper_links: dict[str, list[str]]) -> dict[str, Any]:
    arxiv_ids = paper_links.get("arxiv_ids") or []
    doi_values = paper_links.get("doi") or []
    bibtex_entries = paper_links.get("bibtex_entries") or []
    evidence = [*[f"arXiv:{value}" for value in arxiv_ids], *doi_values, *bibtex_entries]
    if arxiv_ids or doi_values:
        return _judgement("high", "README/config text contains arXiv or DOI identity evidence.", evidence)
    if bibtex_entries:
        return _judgement("medium", "BibTeX citation evidence is present, but arXiv/DOI was not detected.", evidence)
    return _judgement("low", "No arXiv, DOI, or BibTeX identity evidence was detected.", evidence)


def build_inspection_signals(
    metadata: dict[str, Any],
    readme_text: str = "",
    *,
    config_texts: dict[str, str] | None = None,
) -> dict[str, Any]:
    paths = _paths(metadata)
    config_texts = dict(config_texts or {})
    combined_text = " ".join([readme_text, str(metadata.get("readme_text") or ""), *config_texts.values()])
    training_entries = [path for path in paths if _path_matches(path, TRAINING_ENTRY_HINTS)][:12]
    evaluation_entries = [path for path in paths if _path_matches(path, EVAL_ENTRY_HINTS)][:12]
    config_entries = [path for path in paths if _path_matches(path, CONFIG_HINTS)][:12]
    env_lockfiles = [path for path in paths if _path_matches(path, ENV_LOCK_HINTS)][:12]
    environment_files = [path for path in paths if _path_matches(path, ENV_HINTS)][:12]
    reproduction_assets = detect_reproduction_assets({**metadata, "root_paths": paths}, readme_text)
    checkpoint_links = _checkpoint_links(combined_text)
    config_dataset_refs = _config_dataset_refs(config_texts, readme_text)
    paper_links = {
        "arxiv_ids": _arxiv_ids(combined_text),
        "doi": _doi_values(combined_text),
        "bibtex_entries": _bibtex_entries(combined_text),
    }
    instruction_hits = _instruction_evidence(combined_text)
    reproduction_instruction = bool(instruction_hits)
    return {
        "training_entries": training_entries,
        "evaluation_entries": evaluation_entries,
        "config_entries": config_entries,
        "environment_files": environment_files,
        "environment_lockfiles": env_lockfiles,
        "checkpoint_links": checkpoint_links,
        "config_dataset_refs": config_dataset_refs,
        "has_reproduction_instruction": reproduction_instruction,
        "reproduction_instruction_evidence": instruction_hits,
        "paper_links": paper_links,
        "training_readiness": _training_readiness(
            training_entries,
            config_dataset_refs,
            instruction_hits,
            reproduction_assets,
        ),
        "evaluation_readiness": _evaluation_readiness(
            evaluation_entries,
            config_dataset_refs,
            instruction_hits,
            reproduction_assets,
        ),
        "environment_reproducibility": _environment_reproducibility(
            environment_files,
            env_lockfiles,
            reproduction_assets,
        ),
        "paper_identity_confidence": _paper_identity_confidence(paper_links),
        "inspected_config_files": [
            {"path": path, "preview": truncate_text(text, 240)}
            for path, text in list(config_texts.items())[:5]
        ],
        "reproduction_assets": reproduction_assets,
    }
