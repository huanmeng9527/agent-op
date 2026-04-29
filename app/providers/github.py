from __future__ import annotations

import asyncio
import base64
from typing import Any
from urllib.parse import quote

from app.config import get_settings
from app.core.inspection import build_inspection_signals
from app.core.query_analyzer import analyze_query
from app.core.retrieval_profiles import build_github_search_queries, build_repo_aliases
from app.providers.base import BaseProvider
from app.providers.paper_code_identity import PaperCodeIdentityMatch
from app.ranking.scorer import detect_reproduction_assets, score_provider_result
from app.schemas import InspectPaperRepoOutput, ProviderSearchResult, SAFETY_NOTE_TEXT
from app.utils.http import fetch_json
from app.utils.text import truncate_text


class GitHubProvider(BaseProvider):
    name = "github"
    source_type = "github"
    capabilities = frozenset({"repository_search", "repository_inspection"})
    canonical_owners = (
        "facebookresearch",
        "openai",
        "google-research",
        "google-deepmind",
        "nvlabs",
        "microsoft",
        "huggingface",
        "allenai",
        "open-mmlab",
        "mlfoundations",
        "compvis",
        "paddlepaddle",
    )

    def __init__(self) -> None:
        self.settings = get_settings()
        self._search_cache: dict[tuple[str, int], list[dict[str, Any]]] = {}
        self._repo_cache: dict[str, dict[str, Any] | None] = {}
        self._repo_errors: dict[str, str] = {}
        self._readme_cache: dict[str, str] = {}
        self._root_cache: dict[str, list[dict[str, str]]] = {}
        self._tree_cache: dict[str, list[dict[str, str]]] = {}
        self._file_cache: dict[str, str] = {}

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.settings.github_token:
            headers["Authorization"] = f"Bearer {self.settings.github_token}"
        return headers

    def _repo_key(self, owner: str, repo: str) -> str:
        return f"{owner}/{repo}".lower()

    def _repo_to_result(self, repo: dict[str, Any]) -> ProviderSearchResult:
        language = repo.get("language")
        full_name = repo.get("full_name")
        repo_aliases = [full_name, *(repo.get("repo_aliases") or [])]
        metadata = {
            "full_name": full_name,
            "repo_aliases": [alias for alias in repo_aliases if alias],
            "owner": (repo.get("owner") or {}).get("login"),
            "description": repo.get("description") or "",
            "topics": repo.get("topics") or [],
            "languages": [language] if language else [],
            "stargazers_count": repo.get("stargazers_count"),
            "forks_count": repo.get("forks_count"),
            "updated_at": repo.get("updated_at"),
            "pushed_at": repo.get("pushed_at"),
            "archived": repo.get("archived", False),
            "default_branch": repo.get("default_branch"),
        }
        snippet = " | ".join(
            part
            for part in [
                repo.get("description") or "",
                f"stars={repo.get('stargazers_count')}",
                f"updated={repo.get('updated_at')}",
                f"language={language}" if language else "",
            ]
            if part
        )
        return ProviderSearchResult(
            title=repo.get("full_name") or repo.get("name") or "GitHub Repository",
            url=repo.get("html_url") or "",
            source=self.name,
            source_type=self.source_type,
            snippet=truncate_text(snippet, 360),
            metadata=metadata,
        )

    def _attach_repo_alias(self, payload: dict[str, Any], alias: str) -> dict[str, Any]:
        aliases = [
            value
            for value in [alias, payload.get("full_name"), *(payload.get("repo_aliases") or [])]
            if isinstance(value, str) and value.strip()
        ]
        seen: set[str] = set()
        output: list[str] = []
        for value in aliases:
            key = value.strip().casefold()
            if key in seen:
                continue
            seen.add(key)
            output.append(value.strip())
        payload = dict(payload)
        payload["repo_aliases"] = output
        return payload

    def _build_search_queries(self, analysis) -> list[str]:
        return build_github_search_queries(analysis)

    def _canonical_repo_pairs(self, analysis) -> list[tuple[str, str]]:
        pairs: list[tuple[str, str]] = []
        for alias in build_repo_aliases(analysis)[:4]:
            for owner in self.canonical_owners:
                pairs.append((owner, alias))
                if len(pairs) >= 32:
                    return pairs
        return pairs

    async def _fetch_canonical_candidates(self, analysis) -> list[dict[str, Any]]:
        pairs = self._canonical_repo_pairs(analysis)
        if not pairs:
            return []
        fetched = await asyncio.gather(
            *(self._fetch_repository(owner, repo) for owner, repo in pairs),
            return_exceptions=True,
        )
        candidates: list[dict[str, Any]] = []
        for payload in fetched:
            if isinstance(payload, dict) and payload.get("html_url"):
                candidates.append(payload)
        return candidates

    async def _search_repositories(self, query: str, per_page: int) -> list[dict[str, Any]]:
        cache_key = (query, per_page)
        if cache_key in self._search_cache:
            return list(self._search_cache[cache_key])
        payload = await fetch_json(
            f"{self.settings.github_api_base}/search/repositories",
            params={
                "q": query,
                "sort": "best-match",
                "order": "desc",
                "per_page": max(1, min(per_page, 50)),
            },
            headers=self._headers(),
            timeout=self.settings.github_timeout_seconds,
        )
        items = list(payload.get("items") or [])
        self._search_cache[cache_key] = items
        return list(items)

    async def _fetch_repository(self, owner: str, repo: str) -> dict[str, Any] | None:
        key = self._repo_key(owner, repo)
        if key in self._repo_cache:
            cached = self._repo_cache[key]
            return dict(cached) if cached else None
        requested_full_name = f"{owner}/{repo}"
        try:
            payload = await fetch_json(
                f"{self.settings.github_api_base}/repos/{owner}/{repo}",
                headers=self._headers(),
                timeout=self.settings.github_timeout_seconds,
            )
        except Exception as exc:
            moved_payload = await self._fetch_moved_repository(str(exc), requested_full_name)
            if moved_payload is not None:
                self._repo_cache[key] = dict(moved_payload)
                canonical_name = str(moved_payload.get("full_name") or "")
                if "/" in canonical_name:
                    canonical_owner, canonical_repo = canonical_name.split("/", 1)
                    self._repo_cache[self._repo_key(canonical_owner, canonical_repo)] = dict(moved_payload)
                self._repo_errors.pop(key, None)
                return dict(moved_payload)
            self._repo_errors[key] = str(exc)
            self._repo_cache[key] = None
            return None
        payload = self._attach_repo_alias(dict(payload), requested_full_name)
        self._repo_cache[key] = dict(payload)
        self._repo_errors.pop(key, None)
        return dict(payload)

    async def _fetch_moved_repository(self, error: str, requested_full_name: str) -> dict[str, Any] | None:
        if "HTTP 301" not in error or "/repositories/" not in error:
            return None
        match = error.rsplit("url=", 1)
        moved_url = match[-1].strip() if len(match) > 1 else ""
        if not moved_url:
            moved_url = error.rsplit("Source:", 1)[-1].strip()
        if "/repositories/" not in moved_url:
            moved_url = ""
        if not moved_url:
            return None
        try:
            payload = await fetch_json(
                moved_url,
                headers=self._headers(),
                timeout=self.settings.github_timeout_seconds,
            )
        except Exception:
            return None
        if not isinstance(payload, dict) or not payload.get("full_name"):
            return None
        return self._attach_repo_alias(payload, requested_full_name)

    async def _fetch_readme(self, owner: str, repo: str) -> str:
        key = self._repo_key(owner, repo)
        if key in self._readme_cache:
            return self._readme_cache[key]
        try:
            payload = await fetch_json(
                f"{self.settings.github_api_base}/repos/{owner}/{repo}/readme",
                headers=self._headers(),
                timeout=self.settings.github_timeout_seconds,
            )
        except Exception:
            self._readme_cache[key] = ""
            return ""
        content = payload.get("content") or ""
        if (payload.get("encoding") or "").lower() != "base64" or not content:
            self._readme_cache[key] = ""
            return ""
        decoded = base64.b64decode(content).decode("utf-8", errors="replace")
        self._readme_cache[key] = truncate_text(decoded, 2400)
        return self._readme_cache[key]

    async def _fetch_root_entries(self, owner: str, repo: str) -> list[dict[str, str]]:
        key = self._repo_key(owner, repo)
        if key in self._root_cache:
            return list(self._root_cache[key])
        try:
            payload = await fetch_json(
                f"{self.settings.github_api_base}/repos/{owner}/{repo}/contents",
                headers=self._headers(),
                timeout=self.settings.github_timeout_seconds,
            )
        except Exception:
            self._root_cache[key] = []
            return []
        entries_payload = payload.get("entries") if isinstance(payload, dict) else payload
        entries: list[dict[str, str]] = []
        if isinstance(entries_payload, list):
            for entry in entries_payload[:50]:
                if not isinstance(entry, dict):
                    continue
                path = str(entry.get("path") or entry.get("name") or "")
                if path:
                    entries.append(
                        {
                            "path": path,
                            "name": str(entry.get("name") or path),
                            "type": str(entry.get("type") or ""),
                        }
                    )
        self._root_cache[key] = entries
        return list(entries)

    async def _fetch_tree_entries(self, owner: str, repo: str, branch: str | None) -> list[dict[str, str]]:
        key = f"{self._repo_key(owner, repo)}@{branch or 'HEAD'}"
        if key in self._tree_cache:
            return list(self._tree_cache[key])
        if not branch:
            self._tree_cache[key] = []
            return []
        try:
            payload = await fetch_json(
                f"{self.settings.github_api_base}/repos/{owner}/{repo}/git/trees/{quote(branch, safe='')}?recursive=1",
                headers=self._headers(),
                timeout=self.settings.github_timeout_seconds,
            )
        except Exception:
            self._tree_cache[key] = []
            return []
        entries: list[dict[str, str]] = []
        for entry in list(payload.get("tree") or [])[:1000]:
            if not isinstance(entry, dict):
                continue
            path = str(entry.get("path") or "")
            if not path:
                continue
            entry_type = "dir" if entry.get("type") == "tree" else "file" if entry.get("type") == "blob" else str(entry.get("type") or "")
            entries.append({"path": path, "name": path.rsplit("/", 1)[-1], "type": entry_type})
        self._tree_cache[key] = entries
        return list(entries)

    async def _fetch_file_text(self, owner: str, repo: str, path: str) -> str:
        key = f"{self._repo_key(owner, repo)}:{path}"
        if key in self._file_cache:
            return self._file_cache[key]
        try:
            payload = await fetch_json(
                f"{self.settings.github_api_base}/repos/{owner}/{repo}/contents/{quote(path, safe='/')}",
                headers=self._headers(),
                timeout=self.settings.github_timeout_seconds,
            )
        except Exception:
            self._file_cache[key] = ""
            return ""
        content = payload.get("content") if isinstance(payload, dict) else ""
        if not content or (payload.get("encoding") or "").lower() != "base64":
            self._file_cache[key] = ""
            return ""
        decoded = base64.b64decode(content).decode("utf-8", errors="replace")
        self._file_cache[key] = truncate_text(decoded, 2400)
        return self._file_cache[key]

    def _select_config_paths(self, paths: list[str]) -> list[str]:
        selected: list[str] = []
        for path in paths:
            lowered = path.casefold()
            if any(lowered.endswith(suffix) for suffix in (".yaml", ".yml", ".toml")):
                selected.append(path)
            elif lowered.endswith(".json") and any(term in lowered for term in ("config", "dataset", "train", "eval")):
                selected.append(path)
            if len(selected) >= 5:
                break
        return selected

    async def _enrich(self, result: ProviderSearchResult) -> ProviderSearchResult:
        metadata = dict(result.metadata or {})
        full_name = str(metadata.get("full_name") or "")
        if "/" not in full_name:
            return result
        owner, repo = full_name.split("/", 1)
        readme, root_entries = await asyncio.gather(
            self._fetch_readme(owner, repo),
            self._fetch_root_entries(owner, repo),
        )
        metadata["readme_text"] = readme
        metadata["readme_summary"] = truncate_text(readme, 500) if readme else None
        metadata["root_entries"] = root_entries
        metadata["root_paths"] = [entry["path"] for entry in root_entries if entry.get("path")]
        metadata["root_dirs"] = [entry["path"] for entry in root_entries if entry.get("type") == "dir" and entry.get("path")]
        metadata["root_files"] = [entry["path"] for entry in root_entries if entry.get("type") == "file" and entry.get("path")]
        metadata["root_dir_names"] = [entry["name"] for entry in root_entries if entry.get("type") == "dir" and entry.get("name")]
        metadata["root_file_names"] = [entry["name"] for entry in root_entries if entry.get("type") == "file" and entry.get("name")]
        metadata["tree_paths"] = metadata["root_paths"]
        result.metadata = metadata
        result.snippet = truncate_text(
            " | ".join(part for part in [result.snippet, f"README: {readme}" if readme else "", f"ROOT: {', '.join(metadata['root_paths'][:8])}"] if part),
            1600,
        )
        return result

    def _attach_identity_evidence(
        self,
        result: ProviderSearchResult,
        match: PaperCodeIdentityMatch,
    ) -> ProviderSearchResult:
        metadata = dict(result.metadata or {})
        identity = match.to_metadata()
        metadata["external_identity"] = identity
        metadata["external_identity_source"] = match.source
        metadata["external_identity_confidence"] = match.confidence
        metadata["external_identity_evidence"] = match.evidence
        result.metadata = metadata
        result.snippet = truncate_text(
            " | ".join(
                part
                for part in [
                    f"External paper identity evidence: {match.evidence}; confidence={match.confidence}",
                    result.snippet,
                ]
                if part
            ),
            1000,
        )
        return result

    async def fetch_identity_candidates(
        self,
        matches: list[PaperCodeIdentityMatch],
    ) -> list[ProviderSearchResult]:
        results: list[ProviderSearchResult] = []
        seen: set[str] = set()
        for match in matches:
            if "/" not in match.repo:
                continue
            owner, repo = match.repo.split("/", 1)
            payload = await self._fetch_identity_repository(owner, repo)
            if not payload:
                continue
            key = str(payload.get("full_name") or match.repo).casefold()
            if key in seen:
                continue
            seen.add(key)
            results.append(self._attach_identity_evidence(self._repo_to_result(payload), match))
        return await asyncio.gather(*(self._enrich(result) for result in results))

    async def _fetch_identity_repository(self, owner: str, repo: str) -> dict[str, Any] | None:
        key = self._repo_key(owner, repo)
        for attempt in range(5):
            payload = await self._fetch_repository(owner, repo)
            if payload:
                return payload
            error = self._repo_errors.get(key, "")
            if "network error" not in error and "timed out" not in error:
                return None
            self._repo_cache.pop(key, None)
            await asyncio.sleep(min(1.0, 0.25 * (attempt + 1)))
        return None

    def _diversify_by_owner(self, results: list[ProviderSearchResult], *, top_k: int) -> list[ProviderSearchResult]:
        selected: list[ProviderSearchResult] = []
        overflow: list[ProviderSearchResult] = []
        seen_owners: set[str] = set()
        for result in results:
            repo = str((result.metadata or {}).get("full_name") or "")
            owner = repo.split("/", 1)[0].casefold() if "/" in repo else ""
            if owner and owner in seen_owners:
                overflow.append(result)
                continue
            selected.append(result)
            if owner:
                seen_owners.add(owner)
            if len(selected) >= top_k:
                return selected
        for result in overflow:
            selected.append(result)
            if len(selected) >= top_k:
                break
        return selected

    async def search(self, analysis, *, top_k: int = 5) -> list[ProviderSearchResult]:
        items: list[dict[str, Any]] = []
        seen: set[str] = set()
        errors: list[str] = []
        candidate_target = min(50, max(top_k * 8, 16))
        per_query = min(20, max(top_k * 3, 10))
        for repo in await self._fetch_canonical_candidates(analysis):
            key = str(repo.get("full_name") or "").lower()
            if key and key not in seen:
                seen.add(key)
                items.append(repo)
        for query in self._build_search_queries(analysis)[:12]:
            try:
                repos = await self._search_repositories(query, per_page=per_query)
            except Exception as exc:
                errors.append(f"{query}: {exc}")
                continue
            for repo in repos:
                key = str(repo.get("full_name") or "").lower()
                if key and key not in seen:
                    seen.add(key)
                    items.append(repo)
            if len(items) >= candidate_target:
                break
        if not items and errors:
            raise RuntimeError(f"GitHub search failed: {'; '.join(errors[:2])}")
        results = [self._repo_to_result(repo) for repo in items if repo.get("html_url")]
        enrich_limit = min(len(results), max(top_k + 8, 12))
        enriched = await asyncio.gather(*(self._enrich(result) for result in results[:enrich_limit]))
        tail = results[enrich_limit:]
        ranked = [*enriched, *tail]
        ranked.sort(key=lambda item: score_provider_result(analysis, item).score, reverse=True)
        return self._diversify_by_owner(ranked, top_k=top_k)

    async def inspect_repository(
        self,
        repo: str,
        *,
        query: str | None = None,
        include_readme: bool = True,
        include_tree: bool = True,
    ) -> InspectPaperRepoOutput:
        if "/" not in repo:
            return InspectPaperRepoOutput(repo=repo, error="repo must be in owner/name form.", risk_level="high")
        owner, name = repo.split("/", 1)
        payload = await self._fetch_repository(owner, name)
        if payload is None:
            key = self._repo_key(owner, name)
            error = self._repo_errors.get(key) or "Failed to fetch repository."
            return InspectPaperRepoOutput(repo=repo, url=f"https://github.com/{repo}", error=error, risk_level="high")

        result = self._repo_to_result(payload)
        default_branch = str(payload.get("default_branch") or "")
        readme = await self._fetch_readme(owner, name) if include_readme else ""
        root_entries = await self._fetch_root_entries(owner, name) if include_tree else []
        tree_entries = await self._fetch_tree_entries(owner, name, default_branch) if include_tree else []
        metadata = dict(result.metadata or {})
        metadata["readme_text"] = readme
        metadata["readme_summary"] = truncate_text(readme, 500) if readme else None
        metadata["root_entries"] = root_entries
        metadata["root_paths"] = [entry["path"] for entry in root_entries if entry.get("path")]
        metadata["root_dirs"] = [entry["path"] for entry in root_entries if entry.get("type") == "dir" and entry.get("path")]
        metadata["root_files"] = [entry["path"] for entry in root_entries if entry.get("type") == "file" and entry.get("path")]
        metadata["root_dir_names"] = [entry["name"] for entry in root_entries if entry.get("type") == "dir" and entry.get("name")]
        metadata["root_file_names"] = [entry["name"] for entry in root_entries if entry.get("type") == "file" and entry.get("name")]
        metadata["tree_entries"] = tree_entries
        metadata["tree_paths"] = [entry["path"] for entry in tree_entries if entry.get("path")] or metadata["root_paths"]
        metadata["tree_files"] = [entry["path"] for entry in tree_entries if entry.get("type") == "file" and entry.get("path")]
        metadata["tree_dirs"] = [entry["path"] for entry in tree_entries if entry.get("type") == "dir" and entry.get("path")]
        config_paths = self._select_config_paths(metadata["tree_files"])
        config_text_values = await asyncio.gather(*(self._fetch_file_text(owner, name, path) for path in config_paths))
        config_texts = {
            path: text
            for path, text in zip(config_paths, config_text_values, strict=False)
            if text
        }
        result.metadata = metadata
        result.snippet = truncate_text(f"{result.snippet} README: {readme} ROOT: {', '.join(metadata['root_paths'][:10])}", 1800)

        analysis = analyze_query(query or f"{repo} {metadata.get('description') or ''} {readme}")
        explanation = score_provider_result(analysis, result)
        inspection_signals = build_inspection_signals(metadata, readme, config_texts=config_texts)
        assets = inspection_signals["reproduction_assets"]
        fit_for_query = "unknown"
        if query:
            fit_for_query = "high" if explanation.score >= 0.76 else "medium" if explanation.score >= 0.55 else "low"
        suggested_usage = [
            "Use repository structure to plan a clean-room reproduction.",
            "Compare training/evaluation scripts with the paper before trusting reported metrics.",
            "Keep citations and license terms visible in notes and reports.",
        ]
        not_suitable_for = [
            "Directly copying code or experiment claims as your own reproduction.",
            "Treating missing checkpoints or datasets as verified reproducibility evidence.",
        ]
        next_steps = [
            "Read README and installation instructions first.",
            "Check config, dataset, and evaluation scripts before running training.",
            "Record commit hash, environment, and metric differences during reproduction.",
        ]
        return InspectPaperRepoOutput(
            repo=repo,
            url=result.url,
            source_provider=self.name,
            paper_title=analysis.paper_title,
            task=analysis.task,
            repo_role=explanation.repo_role,
            fit_for_query=fit_for_query,
            score=explanation.score,
            value_level=explanation.value_level,
            confidence_level=explanation.confidence_level,
            risk_level=explanation.risk_level,
            risk_note=SAFETY_NOTE_TEXT,
            tech_stack=explanation.tech_stack,
            reproduction_assets=assets,
            inspection_signals=inspection_signals,
            training_readiness=inspection_signals.get("training_readiness", {}),
            evaluation_readiness=inspection_signals.get("evaluation_readiness", {}),
            environment_reproducibility=inspection_signals.get("environment_reproducibility", {}),
            paper_identity_confidence=inspection_signals.get("paper_identity_confidence", {}),
            readme_summary=metadata.get("readme_summary"),
            root_tree=[f"{entry['path']}/" if entry.get("type") == "dir" else entry["path"] for entry in root_entries[:25] if entry.get("path")],
            positive_evidence=explanation.positive_evidence,
            negative_evidence=explanation.negative_evidence,
            suggested_usage=suggested_usage,
            not_suitable_for=not_suitable_for,
            suggested_next_steps=next_steps,
            debug={"analysis": analysis.model_dump(), "metadata": metadata},
        )
