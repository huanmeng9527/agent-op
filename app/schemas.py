from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


SAFETY_NOTE_TEXT = (
    "Results are for paper reproduction research, implementation planning, and source discovery only. "
    "Do not copy repositories, reports, or experiment claims without attribution and independent verification."
)


class QueryAnalysis(BaseModel):
    raw_query: str
    paper_title: str | None = None
    venue: str | None = None
    year: int | None = None
    task: str | None = None
    method_keywords: list[str] = Field(default_factory=list)
    tech_keywords: list[str] = Field(default_factory=list)
    artifact_keywords: list[str] = Field(default_factory=list)
    source_types: list[str] = Field(default_factory=list)


class ProviderSearchResult(BaseModel):
    title: str
    url: str
    source: str
    source_type: str
    snippet: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class PaperMetadata(BaseModel):
    title: str | None = None
    source: str | None = None
    arxiv_id: str | None = None
    doi: str | None = None
    authors: list[str] = Field(default_factory=list)
    published: str | None = None
    summary: str | None = None
    url: str | None = None


class SearchPaperReposInput(BaseModel):
    query: str
    paper_title: str | None = None
    task: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    include_unofficial: bool = True


class SearchResultItem(BaseModel):
    title: str
    url: str
    repo: str | None = None
    source: str
    source_type: str
    snippet: str = ""
    task: str | None = None
    repo_role: str = "unknown"
    tech_stack: list[str] = Field(default_factory=list)
    reproduction_signals: list[str] = Field(default_factory=list)
    reference_utility: list[str] = Field(default_factory=list)
    score: float = 0.0
    value_level: str = "low"
    confidence_level: str = "low"
    cap_reason: str | None = None
    why_recommended: str = ""
    positive_evidence: list[str] = Field(default_factory=list)
    negative_evidence: list[str] = Field(default_factory=list)
    risk_level: str = "medium"
    risk_note: str = SAFETY_NOTE_TEXT
    stars: int | None = None
    updated_at: str | None = None
    language: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchPaperReposOutput(BaseModel):
    query_analysis: QueryAnalysis
    paper_metadata: PaperMetadata | None = None
    total_found: int = 0
    results: list[SearchResultItem] = Field(default_factory=list)
    provider_status: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    safety_note: str = SAFETY_NOTE_TEXT


class InspectPaperRepoInput(BaseModel):
    repo: str = Field(..., description="GitHub repository in owner/name form.")
    query: str | None = None
    include_readme: bool = True
    include_tree: bool = True


class InspectPaperRepoOutput(BaseModel):
    repo: str
    url: str | None = None
    source_provider: str | None = None
    paper_title: str | None = None
    task: str | None = None
    repo_role: str = "unknown"
    fit_for_query: str = "unknown"
    score: float = 0.0
    value_level: str = "low"
    confidence_level: str = "low"
    risk_level: str = "medium"
    risk_note: str = SAFETY_NOTE_TEXT
    tech_stack: list[str] = Field(default_factory=list)
    reproduction_assets: dict[str, bool] = Field(default_factory=dict)
    inspection_signals: dict[str, Any] = Field(default_factory=dict)
    training_readiness: dict[str, Any] = Field(default_factory=dict)
    evaluation_readiness: dict[str, Any] = Field(default_factory=dict)
    environment_reproducibility: dict[str, Any] = Field(default_factory=dict)
    paper_identity_confidence: dict[str, Any] = Field(default_factory=dict)
    paper_metadata: PaperMetadata | None = None
    readme_summary: str | None = None
    root_tree: list[str] = Field(default_factory=list)
    positive_evidence: list[str] = Field(default_factory=list)
    negative_evidence: list[str] = Field(default_factory=list)
    suggested_usage: list[str] = Field(default_factory=list)
    not_suitable_for: list[str] = Field(default_factory=list)
    suggested_next_steps: list[str] = Field(default_factory=list)
    error: str | None = None
    debug: dict[str, Any] = Field(default_factory=dict)


class ComparePaperReposInput(BaseModel):
    repos: list[str] = Field(..., min_length=2, max_length=5)
    query: str | None = None
    criteria: list[str] = Field(default_factory=list)
    include_details: bool = True


class ComparePaperRepoItem(BaseModel):
    repo: str
    url: str | None = None
    repo_role: str = "unknown"
    fit_for_query: str = "unknown"
    score: float = 0.0
    value_level: str = "low"
    risk_level: str = "medium"
    best_for: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    reason: str = ""
    decision_tags: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)
    reproduction_assets: dict[str, bool] = Field(default_factory=dict)
    inspection_signals: dict[str, Any] = Field(default_factory=dict)
    training_readiness: dict[str, Any] = Field(default_factory=dict)
    evaluation_readiness: dict[str, Any] = Field(default_factory=dict)
    environment_reproducibility: dict[str, Any] = Field(default_factory=dict)
    paper_identity_confidence: dict[str, Any] = Field(default_factory=dict)


class FailedRepoItem(BaseModel):
    repo: str
    error: str


class ComparePaperReposOutput(BaseModel):
    query: str | None = None
    criteria: list[str] = Field(default_factory=list)
    best_overall: str | None = None
    summary: str = ""
    comparison: list[ComparePaperRepoItem] = Field(default_factory=list)
    failed_repos: list[FailedRepoItem] = Field(default_factory=list)
    best_for_direct_reproduction: str | None = None
    best_for_method_reference: str | None = None
    best_for_baseline: str | None = None
    not_recommended: list[str] = Field(default_factory=list)
    decision_reasons: dict[str, str] = Field(default_factory=dict)
    recommendation_summary: str = ""
    recommendation: str = ""
    safety_note: str = SAFETY_NOTE_TEXT
