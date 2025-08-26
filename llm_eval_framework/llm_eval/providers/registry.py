"""
Provider registry for managing LLM providers in the LLM evaluation framework.
"""

from typing import Dict, Optional, Type, Union

from .base import BaseProvider, ProviderError
from .litellm_provider import LiteLLMProvider


class ProviderRegistry:
    """Registry for managing LLM providers."""

    def __init__(self):
        """Initialize the provider registry."""
        self._providers: Dict[str, Type[BaseProvider]] = {}
        self._register_default_providers()

    def _register_default_providers(self):
        """Register default providers."""
        # Register LiteLLM as the universal provider for all model types
        self.register("openai", LiteLLMProvider)
        self.register("anthropic", LiteLLMProvider)
        self.register("google", LiteLLMProvider)
        self.register("azure", LiteLLMProvider)
        self.register("cohere", LiteLLMProvider)
        self.register("mistral", LiteLLMProvider)
        self.register("ollama", LiteLLMProvider)
        self.register("huggingface", LiteLLMProvider)
        self.register("replicate", LiteLLMProvider)
        self.register("together", LiteLLMProvider)
        self.register("bedrock", LiteLLMProvider)
        self.register("vertex", LiteLLMProvider)
        self.register("groq", LiteLLMProvider)

    def register(self, name: str, provider_class: Type[BaseProvider]):
        """Register a provider class.

        Args:
            name: Provider name (e.g., "openai", "anthropic")
            provider_class: Provider class
        """
        self._providers[name] = provider_class

    def get_provider_class(self, name: str) -> Optional[Type[BaseProvider]]:
        """Get provider class by name.

        Args:
            name: Provider name

        Returns:
            Provider class or None if not found
        """
        return self._providers.get(name)

    def create_provider(
        self, 
        provider_id: str, 
        config: Optional[Dict] = None
    ) -> BaseProvider:
        """Create a provider instance from provider ID.

        Args:
            provider_id: Provider ID in format "provider:model" (e.g., "openai:gpt-4")
            config: Optional configuration

        Returns:
            Provider instance

        Raises:
            ProviderError: If provider cannot be created
        """
        try:
            # Parse provider ID
            if ":" not in provider_id:
                # Default to LiteLLM for simple model names
                return LiteLLMProvider(model=provider_id, config=config)

            provider_name, model = provider_id.split(":", 1)

            # Get provider class (always LiteLLMProvider now)
            provider_class = self.get_provider_class(provider_name)
            if not provider_class:
                # Use LiteLLM as fallback for unknown providers
                provider_class = LiteLLMProvider

            # For LiteLLM, pass the full model path (provider/model format)
            full_model = f"{provider_name}/{model}" if provider_name != "litellm" else model
            return provider_class(model=full_model, config=config)

        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(
                f"Failed to create provider {provider_id}: {e}",
                provider_name if "provider_name" in locals() else "unknown",
                "creation_failed"
            ) from e

    def list_providers(self) -> Dict[str, Type[BaseProvider]]:
        """List all registered providers.

        Returns:
            Dictionary of provider name to class mappings
        """
        return self._providers.copy()

    def is_provider_available(self, provider_name: str) -> bool:
        """Check if a provider is available.

        Args:
            provider_name: Name of the provider

        Returns:
            True if provider is available
        """
        provider_class = self.get_provider_class(provider_name)
        if not provider_class:
            return False

        # For now, we just check if the class is registered
        # In the future, we could add more sophisticated availability checks
        return True

    def get_supported_models(self, provider_name: str) -> list:
        """Get supported models for a provider.

        Args:
            provider_name: Name of the provider

        Returns:
            List of supported models, or empty list if provider not found
        """
        provider_class = self.get_provider_class(provider_name)
        if not provider_class:
            return []

        # Check if provider has a method to list supported models
        if hasattr(provider_class, "get_available_models"):
            return provider_class.get_available_models()

        return []


# Global provider registry instance
provider_registry = ProviderRegistry()


# Convenience functions
def register_provider(name: str, provider_class: Type[BaseProvider]):
    """Register a provider globally.

    Args:
        name: Provider name
        provider_class: Provider class
    """
    provider_registry.register(name, provider_class)


def create_provider(provider_id: str, config: Optional[Dict] = None) -> BaseProvider:
    """Create a provider instance globally.

    Args:
        provider_id: Provider ID in format "provider:model"
        config: Optional configuration

    Returns:
        Provider instance

    Raises:
        ProviderError: If provider cannot be created
    """
    return provider_registry.create_provider(provider_id, config)


def get_available_providers() -> Dict[str, Type[BaseProvider]]:
    """Get all available providers globally.

    Returns:
        Dictionary of provider name to class mappings
    """
    return provider_registry.list_providers()


def is_provider_available(provider_name: str) -> bool:
    """Check if a provider is available globally.

    Args:
        provider_name: Name of the provider

    Returns:
        True if provider is available
    """
    return provider_registry.is_provider_available(provider_name)