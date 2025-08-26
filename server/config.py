"""
Enhanced configuration management for pgit with LiteLLM integration.

This module extends the original Config class to support LLM API key management
and provider configuration.
"""

import os
import sys
import configparser
from typing import Dict, Any, Optional, List


class Config:
    """Enhanced configuration class for pgit with LiteLLM support."""
    
    def __init__(self, config_file: str):
        """
        Initialize configuration.
        
        Args:
            config_file: Path to the configuration file
        """
        self.config_file = config_file
        
        # Check if config file exists
        if not os.path.exists(self.config_file):
            print(f'config file not found: {self.config_file}', 'error')
            sys.exit(1)

        # Load config file
        print(f'loading config file: {self.config_file}', 'status')
        self.config = configparser.ConfigParser()
        self.config.read(self.config_file)
        
        # Load LLM provider configurations
        self._load_llm_config()
    
    def _load_llm_config(self):
        """Load LLM provider configurations and API keys."""
        # Load API keys from environment variables
        self.api_keys = self._load_api_keys()
        
        # Load provider-specific settings if available in config
        self.provider_settings = self._load_provider_settings()
    
    def _load_api_keys(self) -> Dict[str, Optional[str]]:
        """
        Load API keys from environment variables.
        
        Returns:
            Dictionary mapping provider names to API keys
        """
        api_key_mapping = {
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'google': 'GOOGLE_API_KEY',
            'vertex_ai': 'GOOGLE_API_KEY',  # Vertex AI uses Google API key
            'gemini': 'GOOGLE_API_KEY',     # Gemini uses Google API key
            'azure': 'AZURE_API_KEY',
            'huggingface': 'HUGGINGFACE_API_KEY',
            'cohere': 'COHERE_API_KEY',
            'replicate': 'REPLICATE_API_KEY',
            'together': 'TOGETHER_API_KEY',
            'groq': 'GROQ_API_KEY',
            'perplexity': 'PERPLEXITYAI_API_KEY',
            'mistral': 'MISTRAL_API_KEY',
            'deepseek': 'DEEPSEEK_API_KEY',
            'novita': 'NOVITA_API_KEY',
            'ollama': None,  # Ollama typically doesn't need API keys
            'local': None,   # Local models don't need API keys
        }
        
        api_keys = {}
        for provider, env_var in api_key_mapping.items():
            if env_var:
                api_keys[provider] = os.getenv(env_var)
            else:
                api_keys[provider] = None
        
        return api_keys
    
    def _load_provider_settings(self) -> Dict[str, Dict[str, Any]]:
        """
        Load provider-specific settings from config file.
        
        Returns:
            Dictionary mapping provider names to their settings
        """
        provider_settings = {}
        
        # Check if there's an [llm_providers] section in the config
        if self.config.has_section('llm_providers'):
            for provider in self.config.options('llm_providers'):
                provider_settings[provider] = {}
                
                # Parse provider-specific settings
                provider_config = self.config.get('llm_providers', provider)
                if provider_config:
                    # Simple key=value parsing
                    for setting in provider_config.split(','):
                        if '=' in setting:
                            key, value = setting.strip().split('=', 1)
                            provider_settings[provider][key.strip()] = value.strip()
        
        return provider_settings
    
    def get(self, section: str, key: str) -> Optional[str]:
        """
        Get config option by section and key name.
        
        Args:
            section: Configuration section name
            key: Configuration key name
            
        Returns:
            Configuration value or None if not found
        """
        try:
            return self.config.get(section, key)
        except:
            print(f'config file missing option: {section} {key}', 'error')
            return None
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Get API key for a specific provider.
        
        Args:
            provider: Provider name (e.g., 'openai', 'anthropic')
            
        Returns:
            API key or None if not available
        """
        return self.api_keys.get(provider.lower())
    
    def get_provider_setting(self, provider: str, setting: str) -> Optional[str]:
        """
        Get provider-specific setting.
        
        Args:
            provider: Provider name
            setting: Setting name (e.g., 'api_base', 'api_version')
            
        Returns:
            Setting value or None if not found
        """
        return self.provider_settings.get(provider, {}).get(setting)
    
    def get_available_providers(self) -> List[str]:
        """
        Get list of providers with available API keys.
        
        Returns:
            List of provider names that have API keys configured
        """
        available = []
        for provider, api_key in self.api_keys.items():
            if api_key or provider in ['ollama', 'local']:
                available.append(provider)
        return available
    
    def validate_provider_config(self, provider: str, model: str) -> Dict[str, Any]:
        """
        Validate and return provider configuration for a specific model.
        
        Args:
            provider: Provider name
            model: Model name
            
        Returns:
            Dictionary containing validation results and configuration
            
        Raises:
            ValueError: If provider configuration is invalid
        """
        result = {
            'valid': False,
            'provider': provider,
            'model': model,
            'api_key_available': False,
            'errors': []
        }
        
        # Check if API key is available (if required)
        if provider not in ['ollama', 'local']:
            api_key = self.get_api_key(provider)
            if not api_key:
                result['errors'].append(f'API key not found for provider {provider}')
            else:
                result['api_key_available'] = True
        else:
            result['api_key_available'] = True  # Not required for these providers
        
        # Add any provider-specific validation here
        if provider == 'azure':
            api_base = self.get_provider_setting('azure', 'api_base')
            if not api_base:
                result['errors'].append('Azure API base URL not configured')
        
        # If no errors, configuration is valid
        result['valid'] = len(result['errors']) == 0
        
        return result
    
    def get_llm_config_summary(self) -> Dict[str, Any]:
        """
        Get a summary of LLM configuration status.
        
        Returns:
            Dictionary containing configuration summary
        """
        return {
            'available_providers': self.get_available_providers(),
            'api_key_status': {
                provider: bool(api_key) 
                for provider, api_key in self.api_keys.items()
            },
            'provider_settings': self.provider_settings,
            'total_providers_configured': len(self.get_available_providers())
        }