from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import PROJECT_ROOT
from app.schemas import PaperMetadata, QueryAnalysis
from app.utils.text import unique_preserve_order


DEFAULT_OVERRIDES_PATH = PROJECT_ROOT / "data" / "paper_code_identity_overrides.json"
TITLE_STOPWORDS = {"a", "an", "and", "for", "in", "of", "on", "the", "to", "with"}
GENERIC_TITLE_TOKENS = {
    "algorithm",
    "algorithms",
    "approach",
    "attention",
    "code",
    "data",
    "datasets",
    "deep",
    "framework",
    "image",
    "images",
    "implementation",
    "language",
    "learning",
    "model",
    "models",
    "network",
    "networks",
    "paper",
    "pre",
    "recognition",
    "representation",
    "representations",
    "scale",
    "self",
    "supervised",
    "transformer",
    "transformers",
    "vision",
    "words",
}


@dataclass(frozen=True)
class PaperCodeIdentityMatch:
    repo: str
    source: str
    confidence: str
    evidence: str
    identity_type: str = "official"
    paper_id: str | None = None
    title: str | None = None
    arxiv_id: str | None = None
    note: str | None = None

    def to_metadata(self) -> dict[str, Any]:
        return {
            "repo": self.repo,
            "source": self.source,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "identity_type": self.identity_type,
            "paper_id": self.paper_id,
            "title": self.title,
            "arxiv_id": self.arxiv_id,
            "note": self.note,
        }


def _normalize(value: str | None) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", (value or "").casefold()).split())


def _content_tokens(value: str | None) -> set[str]:
    return {token for token in _normalize(value).split() if token not in TITLE_STOPWORDS}


def _content_token_list(value: str | None) -> list[str]:
    return [token for token in _normalize(value).split() if token not in TITLE_STOPWORDS]


def _specific_tokens(tokens: set[str] | list[str]) -> set[str]:
    return {
        token
        for token in tokens
        if token not in GENERIC_TITLE_TOKENS and not token.isdigit() and len(token) >= 2
    }


def _contains_token_sequence(tokens: list[str], sequence: list[str]) -> bool:
    if not sequence or len(sequence) > len(tokens):
        return False
    sequence_length = len(sequence)
    return any(
        tokens[index:index + sequence_length] == sequence
        for index in range(len(tokens) - sequence_length + 1)
    )


def _is_specific_phrase(tokens: list[str]) -> bool:
    specific = _specific_tokens(tokens)
    return len(specific) >= 2


def _has_strong_title_overlap(alias_tokens: set[str], lookup_tokens: set[str]) -> bool:
    if len(alias_tokens) < 3:
        return False
    overlap = alias_tokens & lookup_tokens
    if len(overlap) / len(alias_tokens) < 0.9:
        return False
    return len(_specific_tokens(overlap)) >= 2


class PaperCodeIdentityProvider:
    name = "paper_code_identity"

    def __init__(self, overrides_path: Path | None = None) -> None:
        self.overrides_path = overrides_path or DEFAULT_OVERRIDES_PATH
        self._overrides: list[dict[str, Any]] | None = None

    def _load_overrides(self) -> list[dict[str, Any]]:
        if self._overrides is not None:
            return list(self._overrides)
        if not self.overrides_path.exists():
            self._overrides = []
            return []
        with self.overrides_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        if not isinstance(payload, list):
            raise ValueError("paper code identity overrides must be a JSON list")
        self._overrides = [entry for entry in payload if isinstance(entry, dict)]
        return list(self._overrides)

    def _matches_title(self, entry: dict[str, Any], lookup_values: list[str]) -> bool:
        title = str(entry.get("title") or "")
        aliases = [title, *(entry.get("title_aliases") or [])]
        for alias in aliases:
            normalized_alias = _normalize(str(alias))
            alias_token_list = _content_token_list(str(alias))
            alias_tokens = set(alias_token_list)
            if not normalized_alias or not alias_tokens:
                continue
            for lookup in lookup_values:
                normalized_lookup = _normalize(lookup)
                if not normalized_lookup:
                    continue
                if normalized_alias == normalized_lookup:
                    return True
                lookup_token_list = _content_token_list(lookup)
                if (
                    _is_specific_phrase(alias_token_list)
                    and _contains_token_sequence(lookup_token_list, alias_token_list)
                ):
                    return True
                lookup_tokens = _content_tokens(lookup)
                if _has_strong_title_overlap(alias_tokens, lookup_tokens):
                    return True
        return False

    def _matches_entry(
        self,
        entry: dict[str, Any],
        *,
        analysis: QueryAnalysis,
        paper_metadata: PaperMetadata | None,
        paper_id: str | None,
        arxiv_id: str | None,
    ) -> bool:
        entry_paper_id = str(entry.get("paper_id") or "")
        entry_arxiv_id = str(entry.get("arxiv_id") or "")
        lookup_values = unique_preserve_order(
            [
                analysis.raw_query,
                analysis.paper_title or "",
                paper_metadata.title if paper_metadata else "",
            ]
        )
        if paper_id and entry_paper_id and _normalize(paper_id) == _normalize(entry_paper_id):
            return True
        if entry_paper_id and any(_normalize(entry_paper_id) in _normalize(value) for value in lookup_values):
            return True
        resolved_arxiv_id = arxiv_id or (paper_metadata.arxiv_id if paper_metadata else None)
        if resolved_arxiv_id and entry_arxiv_id and _normalize(resolved_arxiv_id) == _normalize(entry_arxiv_id):
            return True
        return self._matches_title(entry, lookup_values)

    def resolve(
        self,
        analysis: QueryAnalysis,
        *,
        paper_metadata: PaperMetadata | None = None,
        paper_id: str | None = None,
        arxiv_id: str | None = None,
    ) -> list[PaperCodeIdentityMatch]:
        matches: list[PaperCodeIdentityMatch] = []
        seen_repos: set[str] = set()
        for entry in self._load_overrides():
            if not self._matches_entry(
                entry,
                analysis=analysis,
                paper_metadata=paper_metadata,
                paper_id=paper_id,
                arxiv_id=arxiv_id,
            ):
                continue
            identity_type = str(entry.get("identity_type") or "official")
            repos = entry.get("official_repos") if identity_type == "official" else entry.get("target_repos")
            for repo in repos or []:
                normalized_repo = str(repo).strip()
                if "/" not in normalized_repo:
                    continue
                repo_key = normalized_repo.casefold()
                if repo_key in seen_repos:
                    continue
                seen_repos.add(repo_key)
                source = str(entry.get("source") or "curated_override")
                confidence = str(entry.get("confidence") or "high")
                title = str(entry.get("title") or "") or None
                note = str(entry.get("note") or "") or None
                evidence = str(entry.get("evidence") or "") or None
                evidence_parts = [
                    f"{source} maps this paper identity to {normalized_repo}",
                    f"identity_type: {identity_type}",
                    f"title: {title}" if title else "",
                    f"arxiv: {entry.get('arxiv_id')}" if entry.get("arxiv_id") else "",
                    evidence or "",
                    note or "",
                ]
                matches.append(
                    PaperCodeIdentityMatch(
                        repo=normalized_repo,
                        source=source,
                        confidence=confidence,
                        evidence="; ".join(part for part in evidence_parts if part),
                        identity_type=identity_type,
                        paper_id=str(entry.get("paper_id") or "") or None,
                        title=title,
                        arxiv_id=str(entry.get("arxiv_id") or "") or None,
                        note=note,
                    )
                )
        return matches
