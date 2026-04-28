from __future__ import annotations

import xml.etree.ElementTree as ET
from urllib.parse import urlencode

import httpx

from app.config import get_settings
from app.schemas import PaperMetadata
from app.utils.text import truncate_text


ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


class PaperMetadataProvider:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._cache: dict[str, PaperMetadata | None] = {}

    def _build_url(self, query: str) -> str:
        params = urlencode(
            {
                "search_query": f'ti:"{query}"',
                "start": 0,
                "max_results": 1,
                "sortBy": "relevance",
                "sortOrder": "descending",
            }
        )
        return f"{self.settings.arxiv_api_base}?{params}"

    def _parse_entry(self, entry: ET.Element) -> PaperMetadata:
        title = " ".join((entry.findtext("atom:title", default="", namespaces=ATOM_NS) or "").split())
        summary = " ".join((entry.findtext("atom:summary", default="", namespaces=ATOM_NS) or "").split())
        url = entry.findtext("atom:id", default="", namespaces=ATOM_NS) or None
        arxiv_id = None
        if url and "/abs/" in url:
            arxiv_id = url.rsplit("/abs/", 1)[-1]
        doi = entry.findtext("arxiv:doi", default="", namespaces=ATOM_NS) or None
        authors = [
            " ".join((author.findtext("atom:name", default="", namespaces=ATOM_NS) or "").split())
            for author in entry.findall("atom:author", ATOM_NS)
        ]
        return PaperMetadata(
            title=title or None,
            source="arxiv",
            arxiv_id=arxiv_id,
            doi=doi,
            authors=[author for author in authors if author][:12],
            published=entry.findtext("atom:published", default="", namespaces=ATOM_NS) or None,
            summary=truncate_text(summary, 800) if summary else None,
            url=url,
        )

    async def resolve(self, query: str | None, *, paper_title: str | None = None) -> PaperMetadata | None:
        lookup = (paper_title or query or "").strip()
        if len(lookup) < 6:
            return None
        cache_key = lookup.casefold()
        if cache_key in self._cache:
            return self._cache[cache_key]
        try:
            async with httpx.AsyncClient(timeout=self.settings.github_timeout_seconds) as client:
                response = await client.get(self._build_url(lookup), headers={"User-Agent": self.settings.user_agent})
                response.raise_for_status()
        except Exception:
            self._cache[cache_key] = None
            return None
        root = ET.fromstring(response.text)
        entry = root.find("atom:entry", ATOM_NS)
        if entry is None:
            self._cache[cache_key] = None
            return None
        metadata = self._parse_entry(entry)
        self._cache[cache_key] = metadata
        return metadata
