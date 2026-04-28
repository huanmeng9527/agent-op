from __future__ import annotations

import re

from app.schemas import QueryAnalysis
from app.utils.text import unique_preserve_order


PAPER_CODE_TERMS = [
    "paper code",
    "official code",
    "official implementation",
    "implementation",
    "reproduction",
    "reimplementation",
]

ALIAS_STOPWORDS = {
    "code",
    "paper",
    "pytorch",
    "tensorflow",
    "implementation",
    "reproduction",
    "official",
    "cvpr",
    "iccv",
    "eccv",
    "neurips",
    "icml",
    "iclr",
}

KNOWN_ALIAS_PHRASES = {
    "segment anything": ["segment-anything", "sam"],
    "end to end object detection with transformers": ["detr"],
    "masked autoencoders": ["mae"],
    "training generative adversarial networks with limited data": ["stylegan2-ada", "stylegan2-ada-pytorch"],
}


def _quote_search_term(term: str) -> str:
    cleaned = " ".join((term or "").replace('"', " ").split()).strip()
    if not cleaned:
        return ""
    if " " in cleaned:
        return f'"{cleaned}"'
    return cleaned


def _append_github_qualifiers(query: str, *, search_in: str = "name,description,readme") -> str:
    parts = [" ".join(query.split()).strip()]
    if search_in:
        parts.append(f"in:{search_in}")
    parts.append("archived:false")
    return " ".join(part for part in parts if part).strip()


def _compose_query(terms: list[str], *, search_in: str = "name,description,readme") -> str:
    query = " ".join(
        _quote_search_term(term)
        for term in unique_preserve_order(terms)
        if _quote_search_term(term)
    )
    return _append_github_qualifiers(query, search_in=search_in)


def _slug_variants(term: str) -> list[str]:
    cleaned = " ".join((term or "").replace('"', " ").split()).strip()
    if not cleaned:
        return []
    lower = cleaned.casefold()
    return unique_preserve_order(
        [
            lower.replace(" ", "-"),
            lower.replace(" ", "_"),
            "".join(lower.split()),
        ]
    )


def _identifier_slug_variants(term: str) -> list[str]:
    variants = _slug_variants(term)
    parts = re.findall(r"[A-Z]+(?=[A-Z][a-z]|[0-9]|\b)|[A-Z]?[a-z]+|[0-9]+", term or "")
    if len(parts) > 1:
        lowered = [part.casefold() for part in parts]
        variants.extend(["_".join(lowered), "-".join(lowered), "".join(lowered)])
    return unique_preserve_order(variants)


def _normalize_alias_text(term: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (term or "").casefold()).strip()


def _versioned_acronym_aliases(text: str) -> list[str]:
    aliases: list[str] = []
    for acronym, version in re.findall(r"\b([A-Z][A-Z0-9]{1,8})\s+([0-9]{1,3})\b", text or ""):
        compact = f"{acronym.casefold()}{version}"
        aliases.extend([compact, f"{acronym.casefold()}-{version}"])
    return unique_preserve_order(aliases)


def _explicit_aliases(text: str) -> list[str]:
    aliases: list[str] = []
    for token in re.findall(r"\b[A-Za-z][A-Za-z0-9-]{1,24}\b", text or ""):
        normalized = token.casefold()
        if normalized in ALIAS_STOPWORDS:
            continue
        has_digit = any(char.isdigit() for char in token)
        is_upper_alias = token.isupper() and len(token) >= 2
        is_camel_alias = token[:1].isupper() and any(char.isupper() for char in token[1:])
        if has_digit or is_upper_alias or is_camel_alias:
            aliases.append(normalized)
            aliases.extend(_identifier_slug_variants(token))
    return unique_preserve_order(aliases)


def _known_phrase_aliases(text: str) -> list[str]:
    normalized = _normalize_alias_text(text)
    aliases: list[str] = []
    for phrase, values in KNOWN_ALIAS_PHRASES.items():
        if phrase in normalized:
            aliases.extend(values)
    return aliases


def _title_prefix_aliases(title: str) -> list[str]:
    prefix = re.split(r"[:：]", title or "", maxsplit=1)[0].strip()
    if not prefix or prefix == (title or "").strip():
        return []
    if len(_normalize_alias_text(prefix).split()) > 4:
        return []
    return _identifier_slug_variants(prefix)


def _query_prefix_aliases(raw_query: str, title: str) -> list[str]:
    normalized_query = _normalize_alias_text(raw_query)
    normalized_title = _normalize_alias_text(title)
    if not normalized_query or not normalized_title:
        return []
    title_index = normalized_query.find(normalized_title)
    if title_index <= 0 or title_index > 40:
        return []
    prefix = normalized_query[:title_index].strip()
    if not prefix or len(prefix.split()) > 3:
        return []
    if any(token in ALIAS_STOPWORDS for token in prefix.split()):
        return []
    return _identifier_slug_variants(prefix)


def build_repo_aliases(analysis: QueryAnalysis) -> list[str]:
    aliases: list[str] = []
    raw_query = analysis.raw_query or ""
    title = analysis.paper_title or ""

    aliases.extend(_versioned_acronym_aliases(f"{title} {raw_query}"))
    aliases.extend(_title_prefix_aliases(title))
    aliases.extend(_query_prefix_aliases(raw_query, title))
    aliases.extend(_known_phrase_aliases(f"{title} {raw_query}"))
    aliases.extend(_explicit_aliases(raw_query))
    if title:
        title_words = _normalize_alias_text(title).split()
        if 1 <= len(title_words) <= 4:
            aliases.extend(_slug_variants(title))

    for alias in list(aliases):
        if analysis.tech_keywords and "pytorch" in analysis.tech_keywords and not alias.endswith("-pytorch"):
            aliases.append(f"{alias}-pytorch")
        if "diffusion" in _normalize_alias_text(f"{title} {raw_query}") and alias == "dreambooth":
            aliases.append("dreambooth-stable-diffusion")

    return unique_preserve_order(
        alias.strip("-_").casefold()
        for alias in aliases
        if alias and len(alias.strip("-_")) >= 2
    )[:8]


def _paper_identity_terms(analysis: QueryAnalysis) -> list[str]:
    terms: list[str] = []
    if analysis.paper_title:
        terms.append(analysis.paper_title)
    if analysis.venue:
        terms.append(analysis.venue)
    if analysis.year:
        terms.append(str(analysis.year))
    return terms


def build_github_search_queries(analysis: QueryAnalysis) -> list[str]:
    identity_terms = _paper_identity_terms(analysis)
    tech_terms = analysis.tech_keywords[:3]
    task_terms = [analysis.task.replace("_", " ")] if analysis.task else []
    raw_query = (analysis.raw_query or "").strip()
    repo_aliases = build_repo_aliases(analysis)
    queries: list[str] = []

    for alias in repo_aliases[:5]:
        queries.extend(
            [
                _compose_query([alias], search_in="name"),
                _compose_query([alias, "official code"]),
            ]
        )

    if analysis.paper_title:
        queries.extend(
            [
                _compose_query([analysis.paper_title], search_in="name"),
                *[_compose_query([variant], search_in="name") for variant in _slug_variants(analysis.paper_title)],
                _compose_query([analysis.paper_title, "paper code"]),
                _compose_query([analysis.paper_title, "official implementation"]),
                _compose_query([analysis.paper_title, "reproduction"]),
                _compose_query([analysis.paper_title, *tech_terms]),
                _compose_query([analysis.paper_title, *task_terms, *tech_terms]),
                _compose_query([analysis.paper_title], search_in="readme"),
            ]
        )

    if identity_terms:
        queries.extend(
            [
                _compose_query([*identity_terms, "implementation"]),
                _compose_query([*identity_terms, "code"]),
                _compose_query([*identity_terms, *tech_terms]),
            ]
        )

    if raw_query:
        queries.extend(
            [
                _append_github_qualifiers(raw_query),
                _compose_query([raw_query, "github repository"]),
                _compose_query([raw_query, "reimplementation"]),
            ]
        )

    if task_terms:
        queries.append(_compose_query([*task_terms, "paper code", *tech_terms]))

    for paper_code_term in PAPER_CODE_TERMS[:4]:
        if identity_terms:
            queries.append(_compose_query([*identity_terms[:1], paper_code_term, *tech_terms[:1]]))

    return unique_preserve_order([query for query in queries if query])
