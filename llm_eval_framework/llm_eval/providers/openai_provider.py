"""
OpenAI provider implementation for promptfoo-python.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional

try:
    import openai
    from openai import OpenAI, AsyncOpenAI
except ImportError:
    openai = None
    OpenAI = None
    AsyncOpenAI = None

from .base import BaseProvider, Message, ProviderError, ProviderResponse, ToolCall
from ..config.models import ToolDefinition


class OpenAIProvider(BaseProvider):
    """OpenAI provider implementation."""

    # Pricing data (as of 2024, per 1M tokens)
    MODEL_PRICING = {
        "gpt-4": {"input": 30.0, "output": 60.0},
        "gpt-4-32k": {"input": 60.0, "output": 120.0},
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "gpt-4-turbo-preview": {"input": 10.0, "output": 30.0},
        "gpt-4o": {"input": 5.0, "output": 15.0},
        "gpt-4o-mini": {"input": 0.15, "output": 0.6},
        "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
        "gpt-3.5-turbo-16k": {"input": 3.0, "output": 4.0},
    }

    def __init__(self, model: str, config: Optional[Dict[str, Any]] = None):
        """Initialize OpenAI provider.

        Args:
            model: OpenAI model name
            config: Provider configuration

        Raises:
            ProviderError: If OpenAI library is not installed
        """
        if openai is None:
            raise ProviderError(
                "OpenAI library not installed. Install with: pip install openai",
                "openai",
                "dependency"
            )

        super().__init__(model, config)

        # Initialize OpenAI client
        api_key = config.get("api_key") if config else None
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ProviderError(
                "OpenAI API key not provided. Set OPENAI_API_KEY environment variable.",
                "openai",
                "authentication"
            )

        self.client = AsyncOpenAI(
            api_key=api_key,
            organization=config.get("organization") if config else None,
            base_url=config.get("base_url") if config else None,
        )

    def _get_provider_name(self) -> str:
        """Get provider name."""
        return "openai"

    async def generate(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        tools: Optional[List[ToolDefinition]] = None,
        **kwargs,
    ) -> ProviderResponse:
        """Generate response from OpenAI.

        Args:
            messages: Conversation messages
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling (0-1)
            tools: Available tools for function calling
            **kwargs: Additional OpenAI parameters

        Returns:
            Provider response

        Raises:
            ProviderError: If generation fails
        """
        try:
            start_time = time.time()

            # Convert messages to OpenAI format
            openai_messages = self._convert_messages(messages)

            # Prepare request parameters
            request_params = {
                "model": self.model,
                "messages": openai_messages,
                **kwargs,
            }

            # Add optional parameters
            if temperature is not None:
                request_params["temperature"] = max(0, min(2, temperature))
            if max_tokens is not None:
                request_params["max_tokens"] = max_tokens
            if top_p is not None:
                request_params["top_p"] = max(0, min(1, top_p))

            # Add tools if provided
            if tools:
                request_params["tools"] = self._convert_tools(tools)

            # Make API call
            response = await self.client.chat.completions.create(**request_params)

            # Calculate latency
            latency = time.time() - start_time

            # Extract response content
            choice = response.choices[0]
            content = choice.message.content or ""
            finish_reason = choice.finish_reason

            # Extract tool calls if present
            tool_calls = None
            if choice.message.tool_calls:
                tool_calls = self._extract_tool_calls(choice.message.tool_calls)

            # Calculate cost
            cost = None
            token_usage = None
            if response.usage:
                token_usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
                cost = self.calculate_cost(token_usage)

            return ProviderResponse(
                content=content,
                tool_calls=tool_calls,
                finish_reason=finish_reason,
                cost=cost,
                latency=latency,
                token_usage=token_usage,
                model=self.model,
                provider=self.provider_name,
                raw_response=response.model_dump() if hasattr(response, 'model_dump') else None,
            )

        except openai.APIError as e:
            raise self._create_error(f"OpenAI API error: {e}", "api") from e
        except openai.RateLimitError as e:
            raise self._create_error(f"OpenAI rate limit exceeded: {e}", "rate_limit") from e
        except openai.AuthenticationError as e:
            raise self._create_error(f"OpenAI authentication failed: {e}", "authentication") from e
        except Exception as e:
            raise self._create_error(f"Unexpected error: {e}", "unknown") from e

    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert internal messages to OpenAI format.

        Args:
            messages: Internal message format

        Returns:
            OpenAI message format
        """
        openai_messages = []
        
        for msg in messages:
            openai_msg = {
                "role": msg.role,
                "content": msg.content,
            }
            
            if msg.name:
                openai_msg["name"] = msg.name
            if msg.tool_call_id:
                openai_msg["tool_call_id"] = msg.tool_call_id
                
            openai_messages.append(openai_msg)

        return openai_messages

    def _convert_tools(self, tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """Convert tool definitions to OpenAI format.

        Args:
            tools: Internal tool definitions

        Returns:
            OpenAI tool format
        """
        openai_tools = []
        
        for tool in tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                }
            }
            openai_tools.append(openai_tool)

        return openai_tools

    def _extract_tool_calls(self, openai_tool_calls) -> List[ToolCall]:
        """Extract tool calls from OpenAI response.

        Args:
            openai_tool_calls: OpenAI tool calls

        Returns:
            Internal tool call format
        """
        tool_calls = []
        
        for tc in openai_tool_calls:
            if tc.function:
                try:
                    arguments = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}
                
                tool_call = ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=arguments,
                )
                tool_calls.append(tool_call)

        return tool_calls

    async def validate_config(self) -> bool:
        """Validate OpenAI configuration.

        Returns:
            True if valid

        Raises:
            ProviderError: If configuration is invalid
        """
        try:
            # Test with a simple request
            await self.test_connection()
            return True
        except Exception as e:
            raise self._create_error(f"Configuration validation failed: {e}", "config") from e

    def get_cost_per_token(self, token_type: str = "input") -> Optional[float]:
        """Get cost per token for this model.

        Args:
            token_type: "input" or "output"

        Returns:
            Cost per token in USD, or None if unknown
        """
        pricing = self.MODEL_PRICING.get(self.model)
        if not pricing:
            # Try to match model name prefix
            for model_name, model_pricing in self.MODEL_PRICING.items():
                if self.model.startswith(model_name):
                    pricing = model_pricing
                    break

        if pricing:
            # Convert from per-1M-tokens to per-token
            return pricing.get(token_type, 0) / 1_000_000

        return None

    @classmethod
    def get_available_models(cls) -> List[str]:
        """Get list of available OpenAI models.

        Returns:
            List of model names
        """
        return [
            "gpt-4",
            "gpt-4-32k",
            "gpt-4-turbo",
            "gpt-4-turbo-preview",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
        ]

    @classmethod
    def supports_model(cls, model: str) -> bool:
        """Check if model is supported.

        Args:
            model: Model name

        Returns:
            True if supported
        """
        available_models = cls.get_available_models()
        return model in available_models or any(
            model.startswith(m) for m in available_models
        )