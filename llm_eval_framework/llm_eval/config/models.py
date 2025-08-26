"""
Configuration models for LLM evaluation framework using Pydantic.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class AssertionType(str, Enum):
    """Types of assertions that can be used in evaluations."""

    CONTAINS = "contains"
    NOT_CONTAINS = "not-contains"
    ICONTAINS = "icontains"  # Case insensitive contains
    COST = "cost"
    LATENCY = "latency"
    LLM_RUBRIC = "llm-rubric"
    JAVASCRIPT = "javascript"
    PYTHON = "python"
    JSON_SCHEMA = "json-schema"
    TOOL_CALLED = "tool-called"
    REGEX = "regex"
    SIMILARITY = "similarity"


class RedTeamPlugin(str, Enum):
    """Available red team plugins."""

    HARMFUL_SELF_HARM = "harmful:self-harm"
    HARMFUL_HATE = "harmful:hate"
    HARMFUL_DRUGS = "harmful:drugs"
    HARMFUL_VIOLENCE = "harmful:violence"
    POLITICS = "politics"
    COMPETITORS = "competitors"
    PII = "pii"
    CUSTOM = "custom"


class RedTeamStrategy(str, Enum):
    """Available red team strategies."""

    JAILBREAK = "jailbreak"
    PROMPT_INJECTION = "prompt-injection"
    USER_MISCHIEF = "user-mischief"
    COMPOSITE = "composite"
    TREE = "tree"


class ToolParameter(BaseModel):
    """Tool parameter definition."""

    type: str
    description: Optional[str] = None
    enum: Optional[List[str]] = None
    required: Optional[bool] = None


class ToolDefinition(BaseModel):
    """Tool definition for function calling."""

    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ProviderConfig(BaseModel):
    """Configuration for an LLM provider."""

    id: str  # Format: "provider:model" or just "provider"
    label: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    tools: Optional[List[ToolDefinition]] = None
    config: Optional[Dict[str, Any]] = None

    @validator("id")
    def validate_id(cls, v):
        """Validate provider ID format."""
        # With LiteLLM, we're more flexible with ID formats
        # Accept both "provider:model" and "provider/model" formats
        if ":" not in v and "/" not in v and not v.startswith("gpt-"):
            # Allow simple model names for backward compatibility
            pass
        return v


class Assertion(BaseModel):
    """Test assertion configuration."""

    type: AssertionType
    value: Optional[Union[str, float, int, Dict[str, Any]]] = None
    threshold: Optional[float] = None
    weight: Optional[float] = 1.0
    description: Optional[str] = None

    @validator("threshold")
    def validate_threshold(cls, v, values):
        """Validate threshold is provided for assertions that need it."""
        assertion_type = values.get("type")
        if assertion_type in [AssertionType.COST, AssertionType.LATENCY] and v is None:
            raise ValueError(f"Threshold required for {assertion_type} assertion")
        return v


class TestCase(BaseModel):
    """Individual test case configuration."""

    description: Optional[str] = None
    vars: Optional[Dict[str, Any]] = Field(default_factory=dict)
    assert_: Optional[List[Assertion]] = Field(default_factory=list, alias="assert")
    threshold: Optional[float] = None
    weight: Optional[float] = 1.0
    options: Optional[Dict[str, Any]] = None


class RedTeamConfig(BaseModel):
    """Red team testing configuration."""

    purpose: Optional[str] = None
    plugins: Optional[List[Union[RedTeamPlugin, str]]] = Field(default_factory=list)
    strategies: Optional[List[Union[RedTeamStrategy, str]]] = Field(default_factory=list)
    numTests: Optional[int] = Field(default=10, alias="num_tests")
    config: Optional[Dict[str, Any]] = None


class DefaultTestConfig(BaseModel):
    """Default test configuration applied to all tests."""

    assert_: Optional[List[Assertion]] = Field(default_factory=list, alias="assert")
    threshold: Optional[float] = None
    weight: Optional[float] = 1.0
    options: Optional[Dict[str, Any]] = None


class OutputConfig(BaseModel):
    """Output configuration for results."""

    path: Optional[str] = None
    format: Optional[str] = "json"
    web: Optional[bool] = True


class LLMEvalConfig(BaseModel):
    """Main configuration model for LLM evaluation framework."""

    # Schema validation
    yaml_language_server: Optional[str] = Field(
        default=None, alias="yaml-language-server"
    )

    # Basic configuration
    description: Optional[str] = None
    version: Optional[str] = "1.0"

    # Prompts and providers
    prompts: List[Union[str, Dict[str, Any]]] = Field(default_factory=list)
    providers: List[Union[str, ProviderConfig]] = Field(default_factory=list)

    # Test configuration
    tests: Optional[List[TestCase]] = Field(default_factory=list)
    defaultTest: Optional[DefaultTestConfig] = Field(
        default=None, alias="default_test"
    )

    # Red team configuration
    redteam: Optional[RedTeamConfig] = Field(default=None)

    # Output configuration
    output: Optional[OutputConfig] = None

    # Advanced configuration
    env: Optional[Dict[str, str]] = Field(default_factory=dict)
    evaluateOptions: Optional[Dict[str, Any]] = Field(
        default_factory=dict, alias="evaluate_options"
    )

    class Config:
        """Pydantic configuration."""

        allow_population_by_field_name = True
        extra = "forbid"
        json_encoders = {
            # Custom encoders if needed
        }

    @validator("providers", pre=True)
    def validate_providers(cls, v):
        """Convert string providers to ProviderConfig objects."""
        result = []
        for provider in v:
            if isinstance(provider, str):
                result.append(ProviderConfig(id=provider))
            else:
                result.append(provider)
        return result

    @validator("prompts")
    def validate_prompts(cls, v):
        """Ensure prompts list is not empty."""
        if not v:
            raise ValueError("At least one prompt must be specified")
        return v

    def get_provider_by_id(self, provider_id: str) -> Optional[ProviderConfig]:
        """Get provider configuration by ID."""
        for provider in self.providers:
            if isinstance(provider, ProviderConfig) and provider.id == provider_id:
                return provider
            elif isinstance(provider, str) and provider == provider_id:
                return ProviderConfig(id=provider_id)
        return None


class EvaluationResult(BaseModel):
    """Result of a single evaluation."""

    provider_id: str
    prompt: str
    vars: Dict[str, Any]
    response: str
    cost: Optional[float] = None
    latency: Optional[float] = None
    assertion_results: List[Dict[str, Any]] = Field(default_factory=list)
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvaluationSummary(BaseModel):
    """Summary of evaluation results."""

    config: LLMEvalConfig
    results: List[EvaluationResult]
    total_tests: int
    passed_tests: int
    failed_tests: int
    total_cost: Optional[float] = None
    average_latency: Optional[float] = None
    timestamp: str
    version: str = "0.1.0"

    @property
    def pass_rate(self) -> float:
        """Calculate pass rate."""
        if self.total_tests == 0:
            return 0.0
        return self.passed_tests / self.total_tests

    def get_results_by_provider(self, provider_id: str) -> List[EvaluationResult]:
        """Get results filtered by provider."""
        return [r for r in self.results if r.provider_id == provider_id]