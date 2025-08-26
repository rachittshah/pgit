"""
Base provider interface for LLM providers in promptfoo-python.
"""

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from ..config.models import ToolDefinition


class Message(BaseModel):
    """Represents a message in a conversation."""

    role: str  # "system", "user", "assistant", "tool"
    content: str
    name: Optional[str] = None  # For tool calls
    tool_call_id: Optional[str] = None  # For tool responses


class ToolCall(BaseModel):
    """Represents a tool call made by the LLM."""

    id: str
    name: str
    arguments: Dict[str, Any]


class ProviderResponse(BaseModel):
    """Response from an LLM provider."""

    content: str
    role: str = "assistant"
    tool_calls: Optional[List[ToolCall]] = None
    finish_reason: Optional[str] = None
    
    # Metadata
    cost: Optional[float] = None
    latency: Optional[float] = None
    token_usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    
    # Raw response for debugging
    raw_response: Optional[Dict[str, Any]] = None


class ProviderError(Exception):
    """Base exception for provider errors."""

    def __init__(self, message: str, provider: str, error_type: str = "unknown"):
        super().__init__(message)
        self.provider = provider
        self.error_type = error_type


class BaseProvider(ABC):
    """Abstract base class for all LLM providers."""

    def __init__(self, model: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the provider.

        Args:
            model: Model identifier (e.g., "gpt-4", "claude-3-sonnet")
            config: Provider-specific configuration
        """
        self.model = model
        self.config = config or {}
        self.provider_name = self._get_provider_name()

    @abstractmethod
    def _get_provider_name(self) -> str:
        """Get the name of this provider."""
        pass

    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        tools: Optional[List[ToolDefinition]] = None,
        **kwargs,
    ) -> ProviderResponse:
        """Generate a response from the LLM.

        Args:
            messages: Conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            tools: Available tools for function calling
            **kwargs: Additional provider-specific parameters

        Returns:
            Provider response

        Raises:
            ProviderError: If generation fails
        """
        pass

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> ProviderResponse:
        """Generate a response from a text prompt.

        Args:
            prompt: Input prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            Provider response

        Raises:
            ProviderError: If generation fails
        """
        messages = []
        
        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))
        
        messages.append(Message(role="user", content=prompt))

        return await self.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    @abstractmethod
    async def validate_config(self) -> bool:
        """Validate the provider configuration.

        Returns:
            True if configuration is valid

        Raises:
            ProviderError: If configuration is invalid
        """
        pass

    def get_cost_per_token(self, token_type: str = "input") -> Optional[float]:
        """Get the cost per token for this model.

        Args:
            token_type: Type of token ("input" or "output")

        Returns:
            Cost per token in USD, or None if unknown
        """
        # Override in subclasses with actual pricing data
        return None

    def calculate_cost(self, token_usage: Dict[str, int]) -> Optional[float]:
        """Calculate the cost of a request based on token usage.

        Args:
            token_usage: Dictionary with token counts

        Returns:
            Total cost in USD, or None if cannot be calculated
        """
        input_cost_per_token = self.get_cost_per_token("input")
        output_cost_per_token = self.get_cost_per_token("output")

        if not input_cost_per_token or not output_cost_per_token:
            return None

        input_tokens = token_usage.get("prompt_tokens", 0)
        output_tokens = token_usage.get("completion_tokens", 0)

        total_cost = (
            input_tokens * input_cost_per_token +
            output_tokens * output_cost_per_token
        )

        return total_cost

    def _create_error(self, message: str, error_type: str = "unknown") -> ProviderError:
        """Create a provider-specific error.

        Args:
            message: Error message
            error_type: Type of error

        Returns:
            Provider error instance
        """
        return ProviderError(message, self.provider_name, error_type)

    async def test_connection(self) -> bool:
        """Test the connection to the provider.

        Returns:
            True if connection is successful

        Raises:
            ProviderError: If connection fails
        """
        try:
            # Simple test with minimal tokens
            response = await self.generate_text(
                prompt="Hello",
                max_tokens=1,
                temperature=0,
            )
            return response is not None
        except Exception as e:
            raise self._create_error(f"Connection test failed: {e}", "connection") from e

    def __str__(self) -> str:
        """String representation of the provider."""
        return f"{self.provider_name}:{self.model}"

    def __repr__(self) -> str:
        """Detailed representation of the provider."""
        return f"{self.__class__.__name__}(model='{self.model}', config={self.config})"