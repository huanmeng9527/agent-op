from app.providers.github import GitHubProvider
from app.providers.registry import ProviderRegistry


def test_registry_filters_by_provider_capability() -> None:
    registry = ProviderRegistry(providers=[GitHubProvider()])

    search_providers = registry.for_capability("repository_search")
    inspection_providers = registry.for_capability("repository_inspection")

    assert [provider.name for provider in search_providers] == ["github"]
    assert [provider.name for provider in inspection_providers] == ["github"]
