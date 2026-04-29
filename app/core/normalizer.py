from __future__ import annotations

from app.ranking.scorer import score_provider_result
from app.schemas import ProviderSearchResult, QueryAnalysis, SAFETY_NOTE_TEXT, SearchResultItem
from app.utils.text import truncate_text, unique_preserve_order


def normalize_provider_result(analysis: QueryAnalysis, result: ProviderSearchResult) -> SearchResultItem:
    explanation = score_provider_result(analysis, result)
    metadata = dict(result.metadata or {})
    metadata["repo_role"] = explanation.repo_role
    identity = metadata.get("external_identity") if isinstance(metadata.get("external_identity"), dict) else {}
    identity_evidence = [str(identity.get("evidence"))] if identity.get("evidence") else []
    full_name = metadata.get("full_name")
    repo_aliases = unique_preserve_order(
        [
            str(full_name or ""),
            *[str(alias) for alias in metadata.get("repo_aliases") or []],
        ]
    )
    return SearchResultItem(
        title=result.title,
        url=result.url,
        repo=full_name,
        repo_aliases=repo_aliases,
        source=result.source,
        source_type=result.source_type,
        snippet=truncate_text(result.snippet, 500),
        task=analysis.task,
        repo_role=explanation.repo_role,
        tech_stack=explanation.tech_stack,
        reproduction_signals=explanation.reproduction_signals,
        reference_utility=explanation.reference_utility,
        score=explanation.score,
        value_level=explanation.value_level,
        confidence_level=explanation.confidence_level,
        identity_source=str(identity.get("source")) if identity.get("source") else None,
        identity_confidence=str(identity.get("confidence")) if identity.get("confidence") else None,
        identity_type=str(identity.get("identity_type")) if identity.get("identity_type") else None,
        identity_evidence=identity_evidence,
        cap_reason=explanation.cap_reason,
        why_recommended=explanation.why_recommended,
        positive_evidence=unique_preserve_order([*identity_evidence, *explanation.positive_evidence]),
        negative_evidence=explanation.negative_evidence,
        risk_level=explanation.risk_level,
        risk_note=SAFETY_NOTE_TEXT,
        stars=metadata.get("stargazers_count"),
        updated_at=metadata.get("updated_at"),
        language=(metadata.get("languages") or [None])[0],
        metadata=metadata,
    )


def dedupe_results(results: list[SearchResultItem]) -> list[SearchResultItem]:
    seen: set[str] = set()
    output: list[SearchResultItem] = []
    for item in results:
        key = (item.repo or item.url).rstrip("/").casefold()
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output
