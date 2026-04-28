from __future__ import annotations

from pydantic import BaseModel, Field


class ScoreExplanation(BaseModel):
    score: float
    value_level: str
    confidence_level: str
    risk_level: str
    repo_role: str
    cap_reason: str | None = None
    tech_stack: list[str] = Field(default_factory=list)
    reproduction_signals: list[str] = Field(default_factory=list)
    reference_utility: list[str] = Field(default_factory=list)
    positive_evidence: list[str] = Field(default_factory=list)
    negative_evidence: list[str] = Field(default_factory=list)
    why_recommended: str = ""
