from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "paper-reproduction-intelligence-mcp-server"
    app_env: str = "dev"
    log_level: str = "INFO"
    github_token: str | None = None
    github_api_base: str = "https://api.github.com"
    github_timeout_seconds: float = 20.0
    arxiv_api_base: str = "https://export.arxiv.org/api/query"
    default_top_k: int = 5
    max_top_k: int = 20
    user_agent: str = "PaperReproductionIntelligenceMCP/0.1.0"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
