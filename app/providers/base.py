from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas import InspectPaperRepoOutput, ProviderSearchResult, QueryAnalysis


class BaseProvider(ABC):
    name: str
    source_type: str
    capabilities: frozenset[str] = frozenset({"repository_search"})

    def supports(self, capability: str) -> bool:
        return capability in self.capabilities

    @abstractmethod
    async def search(self, analysis: QueryAnalysis, *, top_k: int = 5) -> list[ProviderSearchResult]:
        raise NotImplementedError

    async def inspect_repository(
        self,
        repo: str,
        *,
        query: str | None = None,
        include_readme: bool = True,
        include_tree: bool = True,
    ) -> InspectPaperRepoOutput:
        raise NotImplementedError(f"{self.name} does not support repository inspection")
