"""
LLM Service for pgit integration with LiteLLM.

This module provides a service layer for executing prompts using LiteLLM's
unified interface to multiple LLM providers.
"""

import os
import re
import time
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

import litellm
from litellm import completion
import yaml


class LLMService:
    """Service for executing prompts using LiteLLM."""
    
    def __init__(self):
        """Initialize the LLM service."""
        # Enable logging for better debugging
        litellm.set_verbose = False
        
        # Configure success and failure callbacks if needed
        # litellm.success_callback = []
        # litellm.failure_callback = []
    
    def _format_model_identifier(self, provider: str, model: str) -> str:
        """
        Format the model identifier for LiteLLM based on provider and model.
        
        Args:
            provider: The LLM provider (e.g., 'openai', 'anthropic', 'google')
            model: The specific model name
            
        Returns:
            Formatted model identifier for LiteLLM
        """
        # Handle special cases and provider mappings
        provider_mappings = {
            'local': model,  # Use model name directly for local models
            'openai': f'openai/{model}' if not model.startswith('gpt-') else model,
            'anthropic': f'anthropic/{model}' if not model.startswith('claude-') else model,
            'google': f'vertex_ai/{model}' if model.startswith('gemini') else f'google/{model}',
            'azure': f'azure/{model}',
            'huggingface': f'huggingface/{model}',
            'ollama': f'ollama/{model}',
        }
        
        return provider_mappings.get(provider, f'{provider}/{model}')
    
    def _substitute_variables(self, prompt_text: str, input_variables: Dict[str, Any]) -> str:
        """
        Substitute variables in the prompt text with provided values.
        
        Args:
            prompt_text: The prompt template with {variable} placeholders
            input_variables: Dictionary of variable names and values
            
        Returns:
            Prompt text with variables substituted
            
        Raises:
            ValueError: If required variables are missing
        """
        # Find all variables in the prompt text
        variables_in_prompt = set(re.findall(r'\{(\w+)\}', prompt_text))
        
        # Check if all required variables are provided
        missing_variables = variables_in_prompt - set(input_variables.keys())
        if missing_variables:
            raise ValueError(f"Missing required variables: {', '.join(missing_variables)}")
        
        # Substitute variables
        substituted_text = prompt_text
        for var_name, var_value in input_variables.items():
            substituted_text = substituted_text.replace(f'{{{var_name}}}', str(var_value))
        
        return substituted_text
    
    def _prepare_messages(self, prompt_text: str, model_format: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Prepare messages in the appropriate format for the model.
        
        Args:
            prompt_text: The processed prompt text
            model_format: Optional format hint (e.g., 'chat', 'instruct')
            
        Returns:
            List of message dictionaries in OpenAI chat format
        """
        # For now, treat all prompts as user messages
        # In the future, we could parse system/user/assistant roles from the prompt
        return [{"role": "user", "content": prompt_text}]
    
    def _extract_model_settings(self, model_settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and validate model settings for LiteLLM.
        
        Args:
            model_settings: Raw model settings from prompt metadata
            
        Returns:
            Cleaned model settings compatible with LiteLLM
        """
        # Map pgit model settings to LiteLLM parameters
        litellm_params = {}
        
        setting_mappings = {
            'temperature': 'temperature',
            'top_k': 'top_k',
            'top_p': 'top_p',
            'max_tokens': 'max_tokens',
            'stream': 'stream',
            'presence_penalty': 'presence_penalty',
            'frequency_penalty': 'frequency_penalty',
        }
        
        for pgit_key, litellm_key in setting_mappings.items():
            if pgit_key in model_settings:
                litellm_params[litellm_key] = model_settings[pgit_key]
        
        return litellm_params
    
    async def execute_prompt(
        self, 
        prompt_data: Dict[str, Any], 
        input_variables: Dict[str, Any], 
        override_settings: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a prompt using LiteLLM.
        
        Args:
            prompt_data: The complete prompt data from YAML
            input_variables: Variables to substitute in the prompt
            override_settings: Optional settings to override prompt defaults
            stream: Whether to stream the response
            
        Returns:
            Dictionary containing the response and metadata
            
        Raises:
            ValueError: If required data is missing or invalid
            Exception: If LLM execution fails
        """
        start_time = time.time()
        
        try:
            # Extract required fields
            provider = prompt_data.get('provider', 'openai')
            model = prompt_data.get('model', 'gpt-3.5-turbo')
            prompt_text = prompt_data.get('prompt', '')
            model_settings = prompt_data.get('model_settings', {})
            
            # Substitute variables in prompt
            processed_prompt = self._substitute_variables(prompt_text, input_variables)
            
            # Prepare messages
            messages = self._prepare_messages(processed_prompt)
            
            # Prepare model identifier
            model_identifier = self._format_model_identifier(provider, model)
            
            # Prepare settings
            settings = self._extract_model_settings(model_settings)
            if override_settings:
                settings.update(override_settings)
            
            # Add stream setting
            settings['stream'] = stream
            
            # Execute the completion
            response = completion(
                model=model_identifier,
                messages=messages,
                **settings
            )
            
            execution_time = time.time() - start_time
            
            # Format the response
            if stream:
                # For streaming, we'll return the response object directly
                # The caller will need to handle the streaming
                return {
                    'response': response,
                    'metadata': {
                        'prompt_id': prompt_data.get('uuid'),
                        'prompt_title': prompt_data.get('title'),
                        'model': model_identifier,
                        'provider': provider,
                        'execution_time': execution_time,
                        'timestamp': datetime.now().isoformat(),
                        'stream': True
                    }
                }
            else:
                # Extract the response content
                response_content = response.choices[0].message.content
                
                # Extract usage information if available
                usage_info = {}
                if hasattr(response, 'usage') and response.usage:
                    usage_info = {
                        'prompt_tokens': response.usage.prompt_tokens,
                        'completion_tokens': response.usage.completion_tokens,
                        'total_tokens': response.usage.total_tokens,
                    }
                    
                    # Calculate cost if available
                    if hasattr(response, '_hidden_params') and 'response_cost' in response._hidden_params:
                        usage_info['cost'] = response._hidden_params['response_cost']
                
                return {
                    'response': response_content,
                    'metadata': {
                        'prompt_id': prompt_data.get('uuid'),
                        'prompt_title': prompt_data.get('title'),
                        'model': model_identifier,
                        'provider': provider,
                        'usage': usage_info,
                        'execution_time': execution_time,
                        'timestamp': datetime.now().isoformat(),
                        'stream': False
                    },
                    'raw_response': response.model_dump() if hasattr(response, 'model_dump') else dict(response)
                }
                
        except Exception as e:
            execution_time = time.time() - start_time
            raise Exception(f"LLM execution failed after {execution_time:.2f}s: {str(e)}")
    
    def get_available_models(self, prompts_data: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Get a list of available models from the prompt data.
        
        Args:
            prompts_data: List of prompt dictionaries
            
        Returns:
            Dictionary mapping providers to their available models
        """
        available_models = {}
        
        for prompt in prompts_data:
            provider = prompt.get('provider', 'unknown')
            model = prompt.get('model', 'unknown')
            
            if provider not in available_models:
                available_models[provider] = []
            
            if model not in available_models[provider]:
                available_models[provider].append(model)
        
        return available_models
    
    def validate_api_keys(self) -> Dict[str, bool]:
        """
        Check which API keys are available in the environment.
        
        Returns:
            Dictionary mapping provider names to API key availability
        """
        api_key_checks = {
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'google': 'GOOGLE_API_KEY',
            'azure': 'AZURE_API_KEY',
            'huggingface': 'HUGGINGFACE_API_KEY',
            'cohere': 'COHERE_API_KEY',
            'replicate': 'REPLICATE_API_KEY',
        }
        
        availability = {}
        for provider, env_var in api_key_checks.items():
            availability[provider] = bool(os.getenv(env_var))
        
        return availability