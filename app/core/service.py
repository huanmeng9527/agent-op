from __future__ import annotations

import asyncio

from app.core.normalizer import dedupe_results, normalize_provider_result
from app.core.query_analyzer import analyze_query
from app.providers.paper_metadata import PaperMetadataProvider
from app.providers.registry import ProviderRegistry
from app.schemas import (
    ComparePaperRepoItem,
    ComparePaperReposInput,
    ComparePaperReposOutput,
    FailedRepoItem,
    InspectPaperRepoInput,
    InspectPaperRepoOutput,
    SearchPaperReposInput,
    SearchPaperReposOutput,
)
from app.utils.text import contains_term, unique_preserve_order


DEFAULT_COMPARE_CRITERIA = [
    "paper match",
    "training code",
    "evaluation code",
    "environment reproducibility",
    "dataset/checkpoint guidance",
    "risk level",
]


class PaperReproductionIntelligenceService:
    def __init__(self) -> None:
        self.registry = ProviderRegistry()
        self.paper_metadata_provider = PaperMetadataProvider()

    @property
    def github(self):
        return self.registry.get("github")

    async def search_paper_repos(self, payload: SearchPaperReposInput) -> SearchPaperReposOutput:
        paper_metadata = await self.paper_metadata_provider.resolve(payload.query, paper_title=payload.paper_title)
        effective_paper_title = payload.paper_title or (paper_metadata.title if paper_metadata else None)
        analysis = analyze_query(
            payload.query,
            paper_title=effective_paper_title,
            task=payload.task,
            source_types=["github"],
        )
        provider_status = {}
        normalized = []
        for provider in self.registry.for_capability("repository_search"):
            try:
                provider_results = await provider.search(analysis, top_k=payload.top_k)
                provider_status[provider.name] = {"ok": True, "result_count": len(provider_results)}
                normalized.extend(normalize_provider_result(analysis, result) for result in provider_results)
            except Exception as exc:
                provider_status[provider.name] = {"ok": False, "error": str(exc), "result_count": 0}

        results = dedupe_results(normalized)
        if not payload.include_unofficial:
            results = [
                item for item in results
                if item.metadata.get("repo_role") != "reproduction"
                and not contains_term(" ".join([item.title, item.snippet, *item.positive_evidence]), "unofficial")
            ]
        results.sort(key=lambda item: item.score, reverse=True)
        warnings = []
        if not results:
            warnings.append("No stable paper reproduction candidates found; try adding the exact paper title, venue, year, or framework.")
        return SearchPaperReposOutput(
            query_analysis=analysis,
            paper_metadata=paper_metadata,
            total_found=len(results),
            results=results[: payload.top_k],
            provider_status=provider_status,
            warnings=warnings,
        )

    async def inspect_paper_repo(self, payload: InspectPaperRepoInput) -> InspectPaperRepoOutput:
        result = await self.github.inspect_repository(
            payload.repo,
            query=payload.query,
            include_readme=payload.include_readme,
            include_tree=payload.include_tree,
        )
        if not result.error:
            result.paper_metadata = await self.paper_metadata_provider.resolve(
                payload.query or result.paper_title,
                paper_title=result.paper_title,
            )
        return result

    def _criterion_hit(self, criterion: str, item: InspectPaperRepoOutput) -> float:
        criterion_text = criterion.casefold()
        assets = item.reproduction_assets or {}
        signals = item.inspection_signals or {}
        training_score = self._judgement_score(item.training_readiness or signals.get("training_readiness"))
        evaluation_score = self._judgement_score(item.evaluation_readiness or signals.get("evaluation_readiness"))
        environment_score = self._judgement_score(
            item.environment_reproducibility or signals.get("environment_reproducibility")
        )
        identity_score = self._judgement_score(item.paper_identity_confidence or signals.get("paper_identity_confidence"))
        if "paper" in criterion_text or "match" in criterion_text:
            fit_score = {"high": 1.0, "medium": 0.65, "low": 0.25}.get(item.fit_for_query, 0.45)
            return max(fit_score, identity_score)
        if "train" in criterion_text or "training" in criterion_text:
            return max(training_score, 0.8 if assets.get("has_training_code") else 0.2)
        if "eval" in criterion_text or "metric" in criterion_text or "benchmark" in criterion_text:
            return max(evaluation_score, 0.8 if assets.get("has_eval_code") or assets.get("has_results") else 0.2)
        if "environment" in criterion_text or "dependency" in criterion_text or "docker" in criterion_text:
            return max(environment_score, 0.8 if assets.get("has_requirements") else 0.2)
        if "dataset" in criterion_text or "checkpoint" in criterion_text:
            has_dataset_or_checkpoint = (
                assets.get("has_dataset_doc")
                or assets.get("has_checkpoint_hint")
                or bool(signals.get("config_dataset_refs"))
                or bool(signals.get("checkpoint_links"))
            )
            return 1.0 if has_dataset_or_checkpoint else 0.2
        if "risk" in criterion_text:
            return {"low": 1.0, "medium": 0.65, "high": 0.2}.get(item.risk_level, 0.5)
        return item.score

    def _judgement_level(self, value: object) -> str:
        if isinstance(value, dict):
            return str(value.get("level") or "unknown")
        if value:
            return str(value)
        return "unknown"

    def _judgement_score(self, value: object) -> float:
        return {
            "ready": 1.0,
            "locked": 1.0,
            "high": 1.0,
            "documented": 0.75,
            "medium": 0.7,
            "partial": 0.65,
            "low": 0.35,
            "missing": 0.1,
            "unknown": 0.35,
        }.get(self._judgement_level(value), 0.35)

    def _item_judgement(self, item: InspectPaperRepoOutput | ComparePaperRepoItem, field: str) -> dict[str, object]:
        direct = getattr(item, field, None)
        if isinstance(direct, dict) and direct:
            return direct
        signals = item.inspection_signals or {}
        value = signals.get(field)
        return value if isinstance(value, dict) else {}

    def _best_for(self, criteria: list[str], item: InspectPaperRepoOutput) -> list[str]:
        return [criterion for criterion in criteria if self._criterion_hit(criterion, item) >= 0.75][:4]

    def _weaknesses(self, criteria: list[str], item: InspectPaperRepoOutput) -> list[str]:
        misses = [criterion for criterion in criteria if self._criterion_hit(criterion, item) <= 0.35]
        return misses[:4] or item.negative_evidence[:4]

    def _decision_tags(self, item: InspectPaperRepoOutput) -> list[str]:
        assets = item.reproduction_assets or {}
        signals = item.inspection_signals or {}
        training_level = self._judgement_level(item.training_readiness or signals.get("training_readiness"))
        evaluation_level = self._judgement_level(item.evaluation_readiness or signals.get("evaluation_readiness"))
        environment_level = self._judgement_level(
            item.environment_reproducibility or signals.get("environment_reproducibility")
        )
        identity_level = self._judgement_level(item.paper_identity_confidence or signals.get("paper_identity_confidence"))
        tags: list[str] = []
        if (
            training_level == "ready"
            and evaluation_level in {"ready", "partial"}
            or assets.get("has_training_code")
            and (assets.get("has_eval_code") or assets.get("has_results"))
        ):
            tags.append("direct_reproduction_candidate")
        if item.repo_role in {"official_implementation", "implementation"}:
            tags.append("method_reference")
        if assets.get("has_eval_code") or signals.get("evaluation_entries"):
            tags.append("baseline_candidate")
        if item.risk_level == "high" or item.score < 0.45 or (training_level == "missing" and evaluation_level == "missing"):
            tags.append("not_recommended")
        if signals.get("has_reproduction_instruction"):
            tags.append("has_reproduction_instruction")
        if signals.get("environment_lockfiles") or environment_level in {"locked", "documented"}:
            tags.append("has_environment_lockfile")
        if identity_level in {"high", "medium"}:
            tags.append("has_paper_identity_evidence")
        return unique_preserve_order(tags)

    def _readiness_fragment(self, item: InspectPaperRepoOutput | ComparePaperRepoItem) -> str:
        training = self._judgement_level(self._item_judgement(item, "training_readiness"))
        evaluation = self._judgement_level(self._item_judgement(item, "evaluation_readiness"))
        environment = self._judgement_level(self._item_judgement(item, "environment_reproducibility"))
        identity = self._judgement_level(self._item_judgement(item, "paper_identity_confidence"))
        return f"training={training}, evaluation={evaluation}, environment={environment}, identity={identity}"

    def _comparison_reason(self, item: InspectPaperRepoOutput) -> str:
        signals = item.inspection_signals or {}
        evidence = [
            self._readiness_fragment(item),
            *item.positive_evidence[:2],
        ]
        if signals.get("checkpoint_links"):
            evidence.append("checkpoint links detected")
        if signals.get("config_dataset_refs"):
            evidence.append("dataset/config references detected")
        return "; ".join(unique_preserve_order(evidence)[:5])

    def _selection_reason(self, repo: str | None, items: list[ComparePaperRepoItem], *, purpose: str) -> str:
        if not repo:
            return f"No inspected repository had enough evidence for {purpose}."
        item = next((candidate for candidate in items if candidate.repo == repo), None)
        if not item:
            return f"{repo} was selected for {purpose}."
        strengths = [*item.decision_tags[:3], *item.best_for[:2]]
        if not strengths:
            strengths = item.reason.split("; ")[:2]
        return f"{repo} is best for {purpose}: {self._readiness_fragment(item)}; evidence: {', '.join(strengths)}."

    def _not_recommended_reason(self, item: ComparePaperRepoItem) -> str:
        reasons = item.weaknesses[:2]
        if item.risk_level == "high":
            reasons.insert(0, "high risk")
        if not reasons:
            training = self._judgement_level(self._item_judgement(item, "training_readiness"))
            evaluation = self._judgement_level(self._item_judgement(item, "evaluation_readiness"))
            if training == "missing" and evaluation == "missing":
                reasons.append("training/evaluation paths missing")
        return ", ".join(unique_preserve_order(reasons)) or item.risk_level

    def _best_direct_reproduction(self, items: list[ComparePaperRepoItem]) -> str | None:
        candidates = [
            item for item in items
            if "direct_reproduction_candidate" in item.decision_tags and item.risk_level != "high"
        ]
        return max(candidates, key=lambda item: item.score).repo if candidates else None

    def _best_method_reference(self, items: list[ComparePaperRepoItem]) -> str | None:
        candidates = [
            item for item in items
            if "method_reference" in item.decision_tags and item.risk_level != "high"
        ]
        return max(candidates, key=lambda item: (item.repo_role == "official_implementation", item.score)).repo if candidates else None

    def _best_baseline(self, items: list[ComparePaperRepoItem]) -> str | None:
        candidates = [
            item for item in items
            if "baseline_candidate" in item.decision_tags and item.risk_level != "high"
        ]
        return max(candidates, key=lambda item: item.score).repo if candidates else None

    async def compare_paper_repos(self, payload: ComparePaperReposInput) -> ComparePaperReposOutput:
        repos = unique_preserve_order(payload.repos)[:5]
        criteria = unique_preserve_order(payload.criteria) or DEFAULT_COMPARE_CRITERIA
        inspected = await asyncio.gather(
            *[
                self.inspect_paper_repo(
                    InspectPaperRepoInput(repo=repo, query=payload.query, include_readme=True, include_tree=True)
                )
                for repo in repos
            ],
            return_exceptions=True,
        )
        comparison: list[ComparePaperRepoItem] = []
        failed: list[FailedRepoItem] = []
        for repo, result in zip(repos, inspected, strict=False):
            if isinstance(result, Exception):
                failed.append(FailedRepoItem(repo=repo, error=str(result)))
                continue
            if result.error:
                failed.append(FailedRepoItem(repo=repo, error=result.error))
                continue
            comparison.append(
                ComparePaperRepoItem(
                    repo=result.repo,
                    url=result.url,
                    repo_role=result.repo_role,
                    fit_for_query=result.fit_for_query,
                    score=result.score,
                    value_level=result.value_level,
                    risk_level=result.risk_level,
                    best_for=self._best_for(criteria, result),
                    weaknesses=self._weaknesses(criteria, result),
                    reason="; ".join(result.positive_evidence[:3]),
                    decision_tags=self._decision_tags(result),
                    tech_stack=result.tech_stack if payload.include_details else [],
                    reproduction_assets=result.reproduction_assets if payload.include_details else {},
                    inspection_signals=result.inspection_signals if payload.include_details else {},
                    training_readiness=result.training_readiness,
                    evaluation_readiness=result.evaluation_readiness,
                    environment_reproducibility=result.environment_reproducibility,
                    paper_identity_confidence=result.paper_identity_confidence,
                )
            )
            comparison[-1].reason = self._comparison_reason(result)
        risk_order = {"low": 0, "medium": 1, "high": 2}
        comparison.sort(key=lambda item: (risk_order.get(item.risk_level, 1), -item.score))
        best = comparison[0].repo if comparison else None
        best_direct = self._best_direct_reproduction(comparison)
        best_method = self._best_method_reference(comparison)
        best_baseline = self._best_baseline(comparison)
        not_recommended = [
            f"{item.repo}: {self._not_recommended_reason(item)}"
            for item in comparison
            if "not_recommended" in item.decision_tags or item.risk_level == "high"
        ][:3]
        decision_reasons = {
            "best_overall": self._selection_reason(best, comparison, purpose="overall use"),
            "direct_reproduction": self._selection_reason(best_direct, comparison, purpose="direct reproduction"),
            "method_reference": self._selection_reason(best_method, comparison, purpose="method reference"),
            "baseline": self._selection_reason(best_baseline, comparison, purpose="baseline comparison"),
            "not_recommended": "; ".join(not_recommended) if not_recommended else "No high-risk repository was flagged.",
        } if comparison else {}
        summary = "No comparable repositories were inspected successfully." if not comparison else (
            f"Best candidate is {best}, based on paper-fit score, runnable reproduction assets, and risk level."
        )
        recommendation_summary = "No comparable repositories were inspected successfully." if not comparison else (
            f"Use {best_direct or best} for direct reproduction, "
            f"{best_method or best} for implementation details, and "
            f"{best_baseline or best} for baseline comparison; verify any flagged risks before running experiments."
        )
        recommendation = (
            "Use the direct reproduction candidate for running experiments, the method-reference candidate for reading "
            "implementation details, and the baseline candidate for metric comparison. Cross-check datasets, checkpoints, "
            "environment files, and paper metadata before trusting results."
            if comparison else
            "Add valid GitHub repositories in owner/name form and retry."
        )
        return ComparePaperReposOutput(
            query=payload.query,
            criteria=criteria,
            best_overall=best,
            summary=summary,
            comparison=comparison,
            failed_repos=failed,
            best_for_direct_reproduction=best_direct,
            best_for_method_reference=best_method,
            best_for_baseline=best_baseline,
            not_recommended=not_recommended,
            decision_reasons=decision_reasons,
            recommendation_summary=recommendation_summary,
            recommendation=recommendation,
        )
