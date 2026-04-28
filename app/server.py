from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from app.config import get_settings
from app.schemas import ComparePaperReposOutput, InspectPaperRepoOutput, SearchPaperReposOutput
from app.tools.paper_tools import compare_paper_repos_tool, inspect_paper_repo_tool, search_paper_repos_tool


def create_mcp_server(*, streamable_http_path: str = "/mcp") -> FastMCP:
    settings = get_settings()
    mcp = FastMCP(
        name="Paper Reproduction Intelligence MCP Server",
        instructions=(
            "A vertical MCP server for discovering, inspecting, and comparing public paper "
            "implementation and reproduction repositories. It supports research planning, "
            "reproducibility assessment, and source-aware comparison, not code copying."
        ),
        log_level=settings.log_level.upper(),
        streamable_http_path=streamable_http_path,
    )

    @mcp.tool(
        name="search_paper_repos",
        description="Search public GitHub repositories that implement or reproduce a research paper.",
        structured_output=True,
    )
    async def search_paper_repos(
        query: str,
        paper_title: str | None = None,
        task: str | None = None,
        top_k: int = 5,
        include_unofficial: bool = True,
    ) -> SearchPaperReposOutput:
        return await search_paper_repos_tool(
            query=query,
            paper_title=paper_title,
            task=task,
            top_k=top_k,
            include_unofficial=include_unofficial,
        )

    @mcp.tool(
        name="inspect_paper_repo",
        description="Inspect one GitHub paper implementation repository for reproducibility assets and risk.",
        structured_output=True,
    )
    async def inspect_paper_repo(
        repo: str,
        query: str | None = None,
        include_readme: bool = True,
        include_tree: bool = True,
    ) -> InspectPaperRepoOutput:
        return await inspect_paper_repo_tool(
            repo=repo,
            query=query,
            include_readme=include_readme,
            include_tree=include_tree,
        )

    @mcp.tool(
        name="compare_paper_repos",
        description="Compare multiple paper implementation repositories for reproduction planning.",
        structured_output=True,
    )
    async def compare_paper_repos(
        repos: list[str],
        query: str | None = None,
        criteria: list[str] | None = None,
        include_details: bool = True,
    ) -> ComparePaperReposOutput:
        return await compare_paper_repos_tool(
            repos=repos,
            query=query,
            criteria=criteria,
            include_details=include_details,
        )

    return mcp
