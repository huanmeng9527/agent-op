from __future__ import annotations

from app.core.service import PaperReproductionIntelligenceService
from app.schemas import (
    ComparePaperReposInput,
    ComparePaperReposOutput,
    InspectPaperRepoInput,
    InspectPaperRepoOutput,
    SearchPaperReposInput,
    SearchPaperReposOutput,
)


service = PaperReproductionIntelligenceService()


async def search_paper_repos_tool(
    query: str,
    paper_title: str | None = None,
    task: str | None = None,
    top_k: int = 5,
    include_unofficial: bool = True,
) -> SearchPaperReposOutput:
    return await service.search_paper_repos(
        SearchPaperReposInput(
            query=query,
            paper_title=paper_title,
            task=task,
            top_k=top_k,
            include_unofficial=include_unofficial,
        )
    )


async def inspect_paper_repo_tool(
    repo: str,
    query: str | None = None,
    include_readme: bool = True,
    include_tree: bool = True,
) -> InspectPaperRepoOutput:
    return await service.inspect_paper_repo(
        InspectPaperRepoInput(
            repo=repo,
            query=query,
            include_readme=include_readme,
            include_tree=include_tree,
        )
    )


async def compare_paper_repos_tool(
    repos: list[str],
    query: str | None = None,
    criteria: list[str] | None = None,
    include_details: bool = True,
) -> ComparePaperReposOutput:
    return await service.compare_paper_repos(
        ComparePaperReposInput(
            repos=repos,
            query=query,
            criteria=criteria or [],
            include_details=include_details,
        )
    )
