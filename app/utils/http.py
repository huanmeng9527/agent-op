from __future__ import annotations

import asyncio
from typing import Any

import httpx

from app.config import get_settings


class FetchJsonError(RuntimeError):
    pass


def _rate_limit_detail(response: httpx.Response, detail: str) -> str:
    lowered = detail.casefold()
    if response.status_code not in {403, 429} and "rate limit" not in lowered:
        return detail
    parts = [detail or "GitHub API rate limit reached"]
    retry_after = response.headers.get("Retry-After")
    reset_at = response.headers.get("X-RateLimit-Reset")
    remaining = response.headers.get("X-RateLimit-Remaining")
    if remaining is not None:
        parts.append(f"remaining={remaining}")
    if retry_after:
        parts.append(f"retry_after={retry_after}s")
    if reset_at:
        parts.append(f"reset_epoch={reset_at}")
    parts.append("set GITHUB_TOKEN in .env for authenticated requests")
    return "; ".join(parts)


async def fetch_json(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
) -> Any:
    settings = get_settings()
    request_headers = {"User-Agent": settings.user_agent, **(headers or {})}
    async with httpx.AsyncClient(timeout=timeout or settings.github_timeout_seconds) as client:
        for attempt in range(2):
            try:
                response = await client.get(url, params=params, headers=request_headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                detail = ""
                try:
                    payload = exc.response.json()
                    detail = str(payload.get("message") or "")
                except ValueError:
                    detail = exc.response.text[:160]
                if exc.response.status_code in {403, 429} and attempt == 0:
                    retry_after = exc.response.headers.get("Retry-After")
                    wait_seconds = float(retry_after) if retry_after and retry_after.isdigit() else 1.5
                    await asyncio.sleep(min(wait_seconds, 3.0))
                    continue
                detail = _rate_limit_detail(exc.response, detail)
                message = f"HTTP {exc.response.status_code}"
                if detail:
                    message = f"{message}: {detail}"
                raise FetchJsonError(message) from exc
            except httpx.TimeoutException as exc:
                raise FetchJsonError("request timed out") from exc
            except httpx.HTTPError as exc:
                raise FetchJsonError(f"network error: {exc.__class__.__name__}") from exc
    raise FetchJsonError("request failed")
