"""
Pydantic models for pgit LiteLLM API requests and responses.

This module defines the data models for API validation and serialization.
"""

from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime


class InferenceRequest(BaseModel):
    """Request model for prompt inference."""
    
    input_variables: Dict[str, Any] = Field(
        default_factory=dict,
        description="Variables to substitute in the prompt template"
    )
    override_settings: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional settings to override prompt defaults"
    )
    stream: bool = Field(
        default=False,
        description="Whether to stream the response"
    )
    include_raw_response: bool = Field(
        default=False,
        description="Whether to include the raw LiteLLM response in the output"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "input_variables": {
                    "document": "This is a sample document to summarize."
                },
                "override_settings": {
                    "temperature": 0.7,
                    "max_tokens": 150
                },
                "stream": False,
                "include_raw_response": False
            }
        }


class UsageInfo(BaseModel):
    """Usage information from LLM response."""
    
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost: Optional[float] = None


class ResponseMetadata(BaseModel):
    """Metadata for inference response."""
    
    prompt_id: Optional[str] = None
    prompt_title: Optional[str] = None
    model: str
    provider: str
    usage: Optional[UsageInfo] = None
    execution_time: float
    timestamp: str
    stream: bool = False


class InferenceResponse(BaseModel):
    """Response model for prompt inference."""
    
    response: Union[str, Any]  # String for regular response, object for streaming
    metadata: ResponseMetadata
    raw_response: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "This document discusses various topics including...",
                "metadata": {
                    "prompt_id": "32a4558d-bb7c-4dc6-ba07-21540b15cf44",
                    "prompt_title": "Summarize text",
                    "model": "openai/gpt-3.5-turbo",
                    "provider": "openai",
                    "usage": {
                        "prompt_tokens": 50,
                        "completion_tokens": 100,
                        "total_tokens": 150,
                        "cost": 0.002
                    },
                    "execution_time": 1.23,
                    "timestamp": "2024-01-01T12:00:00Z",
                    "stream": False
                }
            }
        }


class ModelInfo(BaseModel):
    """Information about an available model."""
    
    provider: str
    model: str
    display_name: Optional[str] = None
    api_key_available: bool = False
    supported_features: Optional[List[str]] = None


class AvailableModelsResponse(BaseModel):
    """Response model for available models endpoint."""
    
    providers: Dict[str, List[str]]
    models: List[ModelInfo]
    total_models: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "providers": {
                    "openai": ["gpt-3.5-turbo", "gpt-4"],
                    "anthropic": ["claude-2", "claude-instant"]
                },
                "models": [
                    {
                        "provider": "openai",
                        "model": "gpt-3.5-turbo",
                        "display_name": "OpenAI GPT-3.5 Turbo",
                        "api_key_available": True,
                        "supported_features": ["chat", "streaming"]
                    }
                ],
                "total_models": 4
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str
    detail: Optional[str] = None
    error_type: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Missing required variable",
                "detail": "The prompt requires variable 'document' but it was not provided",
                "error_type": "ValidationError",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    
    status: str = "healthy"
    version: str = "1.0.0"
    litellm_version: Optional[str] = None
    available_providers: List[str] = []
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ConfigSummaryResponse(BaseModel):
    """Configuration summary response model."""
    
    available_providers: List[str]
    api_key_status: Dict[str, bool]
    provider_settings: Dict[str, Dict[str, Any]]
    total_providers_configured: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "available_providers": ["openai", "anthropic", "ollama"],
                "api_key_status": {
                    "openai": True,
                    "anthropic": True,
                    "google": False
                },
                "provider_settings": {
                    "azure": {
                        "api_base": "https://example.openai.azure.com",
                        "api_version": "2023-05-15"
                    }
                },
                "total_providers_configured": 3
            }
        }


# Validation functions
def validate_prompt_data(prompt_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate prompt data structure.
    
    Args:
        prompt_data: Prompt data dictionary
        
    Returns:
        Validated prompt data
        
    Raises:
        ValueError: If prompt data is invalid
    """
    required_fields = ['prompt', 'provider', 'model']
    missing_fields = [field for field in required_fields if field not in prompt_data]
    
    if missing_fields:
        raise ValueError(f"Missing required fields in prompt data: {', '.join(missing_fields)}")
    
    return prompt_data


def validate_input_variables(prompt_data: Dict[str, Any], input_variables: Dict[str, Any]) -> None:
    """
    Validate that all required input variables are provided.
    
    Args:
        prompt_data: Prompt data dictionary
        input_variables: Provided input variables
        
    Raises:
        ValueError: If required variables are missing
    """
    expected_variables = prompt_data.get('input_variables', [])
    provided_variables = set(input_variables.keys())
    expected_set = set(expected_variables) if isinstance(expected_variables, list) else set()
    
    missing_variables = expected_set - provided_variables
    if missing_variables:
        raise ValueError(f"Missing required variables: {', '.join(missing_variables)}")