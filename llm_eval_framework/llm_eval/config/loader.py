"""
YAML configuration loader for LLM evaluation framework.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Union

import yaml
from pydantic import ValidationError

from .models import LLMEvalConfig


class ConfigLoaderError(Exception):
    """Base exception for configuration loading errors."""

    pass


class ConfigLoader:
    """Load and validate LLM evaluation configurations from YAML files."""

    def __init__(self, base_path: Path = None):
        """Initialize the config loader.

        Args:
            base_path: Base directory for resolving relative file paths
        """
        self.base_path = base_path or Path.cwd()

    def load_config(self, config_path: Union[str, Path]) -> LLMEvalConfig:
        """Load configuration from YAML file.

        Args:
            config_path: Path to the configuration file

        Returns:
            Parsed and validated configuration

        Raises:
            ConfigLoaderError: If configuration cannot be loaded or is invalid
        """
        config_path = Path(config_path)

        if not config_path.exists():
            raise ConfigLoaderError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                raw_config = yaml.safe_load(f)

            if raw_config is None:
                raise ConfigLoaderError("Configuration file is empty")

            # Set base path for resolving relative file references
            self.base_path = config_path.parent

            # Process file references in prompts
            raw_config = self._process_prompts(raw_config)

            # Validate and create configuration object
            config = LLMEvalConfig(**raw_config)

            return config

        except yaml.YAMLError as e:
            raise ConfigLoaderError(f"Invalid YAML syntax: {e}") from e
        except ValidationError as e:
            raise ConfigLoaderError(f"Configuration validation error: {e}") from e
        except Exception as e:
            raise ConfigLoaderError(f"Failed to load configuration: {e}") from e

    def _process_prompts(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Process prompt definitions, loading external files if referenced.

        Args:
            config: Raw configuration dictionary

        Returns:
            Configuration with resolved prompt files
        """
        if "prompts" not in config:
            return config

        processed_prompts = []

        for prompt in config["prompts"]:
            if isinstance(prompt, str):
                if prompt.startswith("file://"):
                    # Load prompt from file
                    file_path = prompt[7:]  # Remove 'file://' prefix
                    resolved_path = self._resolve_path(file_path)
                    loaded_prompt = self._load_prompt_file(resolved_path)
                    processed_prompts.append(loaded_prompt)
                else:
                    # Direct prompt string
                    processed_prompts.append(prompt)
            elif isinstance(prompt, dict):
                # Prompt object - process any file references within it
                processed_prompts.append(self._process_prompt_object(prompt))
            else:
                processed_prompts.append(prompt)

        config["prompts"] = processed_prompts
        return config

    def _process_prompt_object(self, prompt_obj: Dict[str, Any]) -> Dict[str, Any]:
        """Process a prompt object that might contain file references.

        Args:
            prompt_obj: Prompt object dictionary

        Returns:
            Processed prompt object
        """
        processed = prompt_obj.copy()

        # Handle file references in various prompt formats
        if "file" in processed:
            file_path = processed.pop("file")
            resolved_path = self._resolve_path(file_path)
            file_content = self._load_prompt_file(resolved_path)
            processed.update(file_content)

        return processed

    def _load_prompt_file(self, file_path: Path) -> Union[str, Dict[str, Any], List[Any]]:
        """Load prompt content from a file.

        Args:
            file_path: Path to the prompt file

        Returns:
            Loaded prompt content
        """
        if not file_path.exists():
            raise ConfigLoaderError(f"Prompt file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                if file_path.suffix.lower() in [".yaml", ".yml"]:
                    return yaml.safe_load(f)
                else:
                    return f.read().strip()
        except Exception as e:
            raise ConfigLoaderError(f"Failed to load prompt file {file_path}: {e}") from e

    def _resolve_path(self, file_path: str) -> Path:
        """Resolve a file path relative to the base path.

        Args:
            file_path: File path (relative or absolute)

        Returns:
            Resolved absolute path
        """
        path = Path(file_path)
        if path.is_absolute():
            return path
        else:
            return self.base_path / path

    def load_default_config(self) -> PromptfooConfig:
        """Load configuration from default locations.

        Looks for configuration files in the following order:
        1. llmeval.yaml
        2. llmeval.yml
        3. .llmeval.yaml
        4. .llmeval.yml

        Returns:
            Loaded configuration

        Raises:
            ConfigLoaderError: If no configuration file found
        """
        default_names = [
            "llmeval.yaml",
            "llmeval.yml",
            ".llmeval.yaml",
            ".llmeval.yml",
        ]

        for name in default_names:
            config_path = self.base_path / name
            if config_path.exists():
                return self.load_config(config_path)

        raise ConfigLoaderError(
            "No configuration file found. Expected one of: "
            + ", ".join(default_names)
        )

    def validate_config(self, config: PromptfooConfig) -> List[str]:
        """Validate configuration and return any warnings.

        Args:
            config: Configuration to validate

        Returns:
            List of warning messages
        """
        warnings = []

        # Check for empty tests
        if not config.tests and not config.redteam:
            warnings.append("No tests or red team configuration specified")

        # Check provider configurations
        for provider in config.providers:
            if isinstance(provider, str):
                provider_type = provider.split(":")[0]
                if provider_type not in ["openai", "anthropic", "azure", "local"]:
                    warnings.append(f"Unknown provider type: {provider_type}")

        # Check for missing environment variables
        required_env_vars = self._get_required_env_vars(config)
        for var in required_env_vars:
            if not os.getenv(var):
                warnings.append(f"Environment variable {var} not set")

        return warnings

    def _get_required_env_vars(self, config: PromptfooConfig) -> List[str]:
        """Get list of required environment variables based on providers.

        Args:
            config: Configuration to analyze

        Returns:
            List of required environment variable names
        """
        env_vars = []

        for provider in config.providers:
            provider_id = provider.id if hasattr(provider, "id") else str(provider)
            provider_type = provider_id.split(":")[0]

            if provider_type == "openai":
                env_vars.append("OPENAI_API_KEY")
            elif provider_type == "anthropic":
                env_vars.append("ANTHROPIC_API_KEY")
            elif provider_type == "azure":
                env_vars.extend([
                    "AZURE_OPENAI_API_KEY",
                    "AZURE_OPENAI_ENDPOINT",
                ])

        return list(set(env_vars))  # Remove duplicates

    @staticmethod
    def create_example_config() -> PromptfooConfig:
        """Create an example configuration for initialization.

        Returns:
            Example configuration object
        """
        return PromptfooConfig(
            description="Example LLM evaluation configuration",
            prompts=[
                "Hello, {{name}}! How can I help you today?",
            ],
            providers=[
                "openai:gpt-3.5-turbo",
            ],
            tests=[
                {
                    "vars": {"name": "World"},
                    "assert": [
                        {"type": "contains", "value": "Hello"},
                        {"type": "cost", "threshold": 0.01},
                    ],
                }
            ],
        )