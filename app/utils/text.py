from __future__ import annotations

import re


def safe_lower(value: str | None) -> str:
    return (value or "").casefold()


def truncate_text(value: str, limit: int = 800) -> str:
    text = " ".join((value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "..."


def unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        normalized = safe_lower(value.strip())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        output.append(value.strip())
    return output


def words_from_identifier(value: str) -> str:
    return re.sub(r"[-_/.:]+", " ", value or "")


def contains_term(value: str | None, term: str) -> bool:
    haystack = safe_lower(words_from_identifier(value or ""))
    needle = safe_lower(words_from_identifier(term)).strip()
    if not needle:
        return False
    if re.fullmatch(r"[a-z0-9+#.]+", needle):
        return re.search(rf"(?<![a-z0-9+#.]){re.escape(needle)}(?![a-z0-9+#.])", haystack) is not None
    return needle in haystack
