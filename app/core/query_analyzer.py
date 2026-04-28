from __future__ import annotations

import re

from app.schemas import QueryAnalysis
from app.utils.text import contains_term, safe_lower, unique_preserve_order, words_from_identifier


TASK_TERMS = {
    "computer_vision": ["computer vision", "cv", "image", "segmentation", "detection", "depth", "视觉", "分割", "检测"],
    "nlp": ["nlp", "language model", "llm", "transformer", "bert", "gpt", "自然语言", "大语言模型"],
    "speech": ["speech", "audio", "asr", "tts", "语音"],
    "reinforcement_learning": ["reinforcement learning", "rl", "policy", "gym", "强化学习"],
    "recommender": ["recommendation", "recommender", "ranking", "推荐系统"],
    "graph_learning": ["graph neural", "gnn", "node classification", "图神经网络"],
    "time_series": ["time series", "forecasting", "时间序列", "预测"],
    "robotics": ["robot", "control", "planning", "slam", "机器人"],
}

TECH_TERMS = [
    "pytorch",
    "tensorflow",
    "jax",
    "keras",
    "huggingface",
    "transformers",
    "lightning",
    "cuda",
    "opencv",
    "python",
    "matlab",
    "r",
    "docker",
    "conda",
    "wandb",
]

ARTIFACT_TERMS = [
    "official",
    "unofficial",
    "implementation",
    "reproduction",
    "paper",
    "arxiv",
    "code",
    "pretrained",
    "checkpoint",
    "dataset",
    "train",
    "eval",
    "benchmark",
    "复现",
    "论文",
    "代码",
    "数据集",
    "预训练",
]

VENUES = ["cvpr", "iccv", "eccv", "neurips", "icml", "iclr", "acl", "emnlp", "naacl", "sigir", "kdd", "aaai"]


def _find_year(text: str) -> int | None:
    match = re.search(r"\b(20[0-3][0-9])\b", text)
    if not match:
        return None
    return int(match.group(1))


def _find_task(text: str) -> str | None:
    for task, terms in TASK_TERMS.items():
        if any(contains_term(text, term) for term in terms):
            return task
    return None


def _find_terms(text: str, terms: list[str]) -> list[str]:
    return unique_preserve_order([term for term in terms if contains_term(text, term)])


def _infer_paper_title(query: str) -> str | None:
    quoted = re.findall(r"[\"“”']([^\"“”']{6,120})[\"“”']", query)
    if quoted:
        return quoted[0].strip()
    cleaned = re.sub(r"\b(github|code|implementation|reproduction|paper|arxiv|复现|代码|论文)\b", " ", query, flags=re.I)
    cleaned = re.sub(r"\b(20[0-3][0-9]|cvpr|iccv|eccv|neurips|icml|iclr|acl|emnlp|aaai)\b", " ", cleaned, flags=re.I)
    for term in TECH_TERMS:
        cleaned = re.sub(rf"(?<![a-z0-9+#.]){re.escape(term)}(?![a-z0-9+#.])", " ", cleaned, flags=re.I)
    for task_terms in TASK_TERMS.values():
        for term in task_terms:
            if term.isascii():
                cleaned = re.sub(rf"(?<![a-z0-9+#.]){re.escape(term)}(?![a-z0-9+#.])", " ", cleaned, flags=re.I)
            else:
                cleaned = cleaned.replace(term, " ")
    cleaned = " ".join(cleaned.split())
    if 8 <= len(cleaned) <= 120:
        return cleaned
    return None


def analyze_query(
    query: str,
    *,
    paper_title: str | None = None,
    task: str | None = None,
    source_types: list[str] | None = None,
) -> QueryAnalysis:
    text = query or ""
    lowered = safe_lower(text)
    venue = next((venue.upper() for venue in VENUES if venue in lowered), None)
    return QueryAnalysis(
        raw_query=query,
        paper_title=paper_title or _infer_paper_title(text),
        venue=venue,
        year=_find_year(text),
        task=task or _find_task(text),
        method_keywords=_find_terms(text, ARTIFACT_TERMS),
        tech_keywords=_find_terms(text, TECH_TERMS),
        artifact_keywords=_find_terms(text, ARTIFACT_TERMS),
        source_types=source_types or ["github"],
    )
