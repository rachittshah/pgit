"""
LiteLLM provider implementation for universal LLM access.
"""

import time
from typing import Any, Dict, List, Optional

try:
    import litellm
    from litellm import acompletion, completion_cost
except ImportError:
    litellm = None

from .base import BaseProvider, Message, ProviderError, ProviderResponse, ToolCall
from ..config.models import ToolDefinition


class LiteLLMProvider(BaseProvider):
    """Universal LLM provider using LiteLLM."""

    def __init__(self, model: str, config: Optional[Dict[str, Any]] = None):
        """Initialize LiteLLM provider.

        Args:
            model: Model identifier (e.g., "openai/gpt-4", "anthropic/claude-3-sonnet")
            config: Provider configuration

        Raises:
            ProviderError: If LiteLLM library is not installed
        """
        if litellm is None:
            raise ProviderError(
                "LiteLLM library not installed. Install with: pip install litellm",
                "litellm",
                "dependency"
            )

        super().__init__(model, config)

        # Configure LiteLLM settings
        self._configure_litellm()

    def _configure_litellm(self):
        """Configure LiteLLM with global settings."""
        # Set default configurations
        if self.config.get("api_base"):
            litellm.api_base = self.config["api_base"]
        
        # Set timeout
        litellm.request_timeout = self.config.get("timeout", 120)
        
        # Configure retry settings
        litellm.num_retries = self.config.get("num_retries", 3)
        
        # Configure logging level
        if self.config.get("verbose", False):
            litellm.set_verbose = True

    def _get_provider_name(self) -> str:
        """Get provider name from model string."""
        if "/" in self.model:
            return self.model.split("/")[0]
        return "litellm"

    async def generate(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        tools: Optional[List[ToolDefinition]] = None,
        **kwargs,
    ) -> ProviderResponse:
        """Generate response using LiteLLM.

        Args:
            messages: Conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            tools: Available tools for function calling
            **kwargs: Additional parameters

        Returns:
            Provider response

        Raises:
            ProviderError: If generation fails
        """
        try:
            start_time = time.time()

            # Convert messages to LiteLLM format
            litellm_messages = self._convert_messages(messages)

            # Prepare request parameters
            request_params = {
                "model": self.model,
                "messages": litellm_messages,
                **kwargs,
            }

            # Add optional parameters
            if temperature is not None:
                request_params["temperature"] = temperature
            if max_tokens is not None:
                request_params["max_tokens"] = max_tokens
            if top_p is not None:
                request_params["top_p"] = top_p

            # Add tools if provided
            if tools:
                request_params["tools"] = self._convert_tools(tools)

            # Make async API call
            response = await acompletion(**request_params)

            # Calculate latency
            latency = time.time() - start_time

            # Extract response content
            choice = response.choices[0]
            content = choice.message.content or ""
            finish_reason = choice.finish_reason

            # Extract tool calls if present
            tool_calls = None
            if hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
                tool_calls = self._extract_tool_calls(choice.message.tool_calls)

            # Calculate cost using LiteLLM's built-in cost calculation
            cost = None
            token_usage = None
            if hasattr(response, 'usage') and response.usage:
                token_usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
                try:
                    cost = completion_cost(response)
                except Exception:
                    # Fallback if cost calculation fails
                    cost = None

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

        except Exception as e:
            # Handle LiteLLM exceptions
            error_type = "unknown"
            if "rate limit" in str(e).lower():
                error_type = "rate_limit"
            elif "authentication" in str(e).lower() or "api key" in str(e).lower():
                error_type = "authentication"
            elif "not found" in str(e).lower():
                error_type = "not_found"
            elif "timeout" in str(e).lower():
                error_type = "timeout"
            
            raise self._create_error(f"LiteLLM error: {e}", error_type) from e

    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert internal messages to LiteLLM format.

        Args:
            messages: Internal message format

        Returns:
            LiteLLM message format
        """
        litellm_messages = []
        
        for msg in messages:
            litellm_msg = {
                "role": msg.role,
                "content": msg.content,
            }
            
            if msg.name:
                litellm_msg["name"] = msg.name
            if msg.tool_call_id:
                litellm_msg["tool_call_id"] = msg.tool_call_id
                
            litellm_messages.append(litellm_msg)

        return litellm_messages

    def _convert_tools(self, tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """Convert tool definitions to LiteLLM format.

        Args:
            tools: Internal tool definitions

        Returns:
            LiteLLM tool format
        """
        litellm_tools = []
        
        for tool in tools:
            litellm_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                }
            }
            litellm_tools.append(litellm_tool)

        return litellm_tools

    def _extract_tool_calls(self, litellm_tool_calls) -> List[ToolCall]:
        """Extract tool calls from LiteLLM response.

        Args:
            litellm_tool_calls: LiteLLM tool calls

        Returns:
            Internal tool call format
        """
        tool_calls = []
        
        for tc in litellm_tool_calls:
            if hasattr(tc, 'function') and tc.function:
                try:
                    import json
                    arguments = json.loads(tc.function.arguments) if tc.function.arguments else {}
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
        """Validate LiteLLM configuration.

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
        """Get cost per token using LiteLLM's cost calculation.

        Args:
            token_type: "input" or "output"

        Returns:
            Cost per token in USD, or None if unknown
        """
        # LiteLLM handles cost calculation internally
        # We'll rely on the completion_cost function
        return None

    @classmethod
    def get_available_models(cls) -> List[str]:
        """Get list of available models through LiteLLM.

        Returns:
            List of model names
        """
        # Common models available through LiteLLM
        return [
            # OpenAI
            "openai/gpt-4",
            "openai/gpt-4-turbo",
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "openai/gpt-3.5-turbo",
            
            # Anthropic
            "anthropic/claude-3-sonnet",
            "anthropic/claude-3-haiku",
            "anthropic/claude-3-opus",
            "anthropic/claude-3.5-sonnet",
            
            # Google
            "google/gemini-pro",
            "google/gemini-2.0-flash",
            "google/gemini-2.5-pro",
            
            # Azure OpenAI
            "azure/gpt-4",
            "azure/gpt-4-turbo",
            "azure/gpt-35-turbo",
            
            # Mistral
            "mistral/mistral-large-latest",
            "mistral/mistral-medium",
            "mistral/mistral-small",
            
            # Cohere
            "cohere/command-r-plus",
            "cohere/command-r",
            
            # Local/Open Source
            "ollama/llama2",
            "ollama/llama3",
            "ollama/codellama",
            
            # Hugging Face
            "huggingface/microsoft/DialoGPT-medium",
            "huggingface/bigscience/bloom",
        ]

    @classmethod
    def supports_model(cls, model: str) -> bool:
        """Check if model is supported by LiteLLM.

        Args:
            model: Model name

        Returns:
            True if supported (LiteLLM supports many models)
        """
        # LiteLLM supports a wide variety of models
        # We'll be permissive and assume it can handle most model strings
        common_providers = [
            "openai", "anthropic", "google", "azure", "cohere", 
            "mistral", "ollama", "huggingface", "replicate", 
            "together", "bedrock", "vertex", "groq"
        ]
        
        if "/" in model:
            provider = model.split("/")[0]
            return provider in common_providers
        
        # If no provider prefix, assume it's supported
        return True