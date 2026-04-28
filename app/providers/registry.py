from __future__ import annotations

from app.providers.base import BaseProvider
from app.providers.github import GitHubProvider


class ProviderRegistry:
    def __init__(self, providers: list[BaseProvider] | None = None) -> None:
        self._providers = {provider.name: provider for provider in (providers or [GitHubProvider()])}

    def get(self, name: str) -> BaseProvider:
        return self._providers[name]

    def all(self) -> list[BaseProvider]:
        return list(self._providers.values())

    def for_capability(self, capability: str) -> list[BaseProvider]:
        return [provider for provider in self.all() if provider.supports(capability)]
