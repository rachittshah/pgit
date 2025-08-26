"""
Core evaluation engine for promptfoo-python.
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from jinja2 import Template

from ..config.models import (
    Assertion,
    EvaluationResult,
    EvaluationSummary,
    PromptfooConfig,
    TestCase,
)
from ..providers.base import BaseProvider, Message, ProviderError
from ..providers.registry import create_provider
from .assertions.registry import assertion_registry


class EvaluationError(Exception):
    """Exception raised during evaluation."""

    pass


class Evaluator:
    """Core evaluation engine."""

    def __init__(self, config: PromptfooConfig):
        """Initialize the evaluator.

        Args:
            config: Promptfoo configuration
        """
        self.config = config
        self.providers: Dict[str, BaseProvider] = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize all providers from configuration."""
        for provider_config in self.config.providers:
            try:
                if hasattr(provider_config, 'id'):
                    provider_id = provider_config.id
                    config = provider_config.dict() if hasattr(provider_config, 'dict') else {}
                else:
                    provider_id = str(provider_config)
                    config = {}

                provider = create_provider(provider_id, config)
                self.providers[provider_id] = provider

            except Exception as e:
                raise EvaluationError(f"Failed to initialize provider {provider_config}: {e}") from e

    async def evaluate(self) -> EvaluationSummary:
        """Run the complete evaluation.

        Returns:
            Evaluation summary with results

        Raises:
            EvaluationError: If evaluation fails
        """
        if not self.config.tests:
            raise EvaluationError("No tests configured for evaluation")

        all_results = []
        total_tests = 0
        passed_tests = 0

        # Run tests for each prompt-provider combination
        for prompt_template in self.config.prompts:
            for provider_id, provider in self.providers.items():
                for test_case in self.config.tests:
                    total_tests += 1
                    
                    try:
                        result = await self._run_single_test(
                            prompt_template, provider, test_case
                        )
                        all_results.append(result)
                        
                        if result.success:
                            passed_tests += 1
                            
                    except Exception as e:
                        # Create a failed result for the exception
                        result = EvaluationResult(
                            provider_id=provider_id,
                            prompt=str(prompt_template),
                            vars=test_case.vars or {},
                            response="",
                            success=False,
                            error=str(e),
                        )
                        all_results.append(result)

        # Calculate summary statistics
        total_cost = sum(r.cost for r in all_results if r.cost is not None)
        latencies = [r.latency for r in all_results if r.latency is not None]
        average_latency = sum(latencies) / len(latencies) if latencies else None

        return EvaluationSummary(
            config=self.config,
            results=all_results,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=total_tests - passed_tests,
            total_cost=total_cost if total_cost > 0 else None,
            average_latency=average_latency,
            timestamp=datetime.now().isoformat(),
        )

    async def _run_single_test(
        self, 
        prompt_template: Any, 
        provider: BaseProvider, 
        test_case: TestCase
    ) -> EvaluationResult:
        """Run a single test case.

        Args:
            prompt_template: Prompt template (string or dict)
            provider: LLM provider
            test_case: Test case to run

        Returns:
            Evaluation result
        """
        try:
            # Render the prompt with variables
            rendered_prompt = self._render_prompt(prompt_template, test_case.vars or {})

            # Generate response from provider
            provider_response = await provider.generate_text(rendered_prompt)

            # Run assertions
            assertion_results = []
            overall_success = True

            # Combine test-specific and default assertions
            assertions = []
            if self.config.defaultTest and self.config.defaultTest.assert_:
                assertions.extend(self.config.defaultTest.assert_)
            if test_case.assert_:
                assertions.extend(test_case.assert_)

            for assertion in assertions:
                try:
                    assertion_result = await self._run_assertion(
                        assertion, provider_response.content, provider_response
                    )
                    assertion_results.append(assertion_result)
                    
                    if not assertion_result.get("passed", False):
                        overall_success = False
                        
                except Exception as e:
                    assertion_result = {
                        "type": assertion.type,
                        "passed": False,
                        "error": str(e),
                    }
                    assertion_results.append(assertion_result)
                    overall_success = False

            return EvaluationResult(
                provider_id=provider.provider_name + ":" + provider.model,
                prompt=rendered_prompt,
                vars=test_case.vars or {},
                response=provider_response.content,
                cost=provider_response.cost,
                latency=provider_response.latency,
                assertion_results=assertion_results,
                success=overall_success,
                metadata={
                    "model": provider_response.model,
                    "provider": provider_response.provider,
                    "token_usage": provider_response.token_usage,
                    "finish_reason": provider_response.finish_reason,
                },
            )

        except ProviderError as e:
            return EvaluationResult(
                provider_id=provider.provider_name + ":" + provider.model,
                prompt=str(prompt_template),
                vars=test_case.vars or {},
                response="",
                success=False,
                error=f"Provider error: {e}",
            )
        except Exception as e:
            return EvaluationResult(
                provider_id=provider.provider_name + ":" + provider.model,
                prompt=str(prompt_template),
                vars=test_case.vars or {},
                response="",
                success=False,
                error=f"Unexpected error: {e}",
            )

    def _render_prompt(self, prompt_template: Any, variables: Dict[str, Any]) -> str:
        """Render a prompt template with variables.

        Args:
            prompt_template: Template (string or dict)
            variables: Variables for template rendering

        Returns:
            Rendered prompt string
        """
        if isinstance(prompt_template, str):
            # Simple string template
            template = Template(prompt_template)
            return template.render(**variables)
        
        elif isinstance(prompt_template, dict):
            # Structured prompt (e.g., chat format)
            if isinstance(prompt_template, list):
                # List of messages
                rendered_messages = []
                for msg in prompt_template:
                    if isinstance(msg, dict) and "content" in msg:
                        rendered_content = Template(msg["content"]).render(**variables)
                        rendered_msg = msg.copy()
                        rendered_msg["content"] = rendered_content
                        rendered_messages.append(rendered_msg)
                    else:
                        rendered_messages.append(msg)
                return str(rendered_messages)  # Convert to string for now
            else:
                # Single message dict
                if "content" in prompt_template:
                    template = Template(prompt_template["content"])
                    return template.render(**variables)
                else:
                    return str(prompt_template)
        else:
            return str(prompt_template)

    async def _run_assertion(
        self, 
        assertion: Assertion, 
        response_text: str, 
        provider_response: Any
    ) -> Dict[str, Any]:
        """Run a single assertion.

        Args:
            assertion: Assertion to run
            response_text: Response text to check
            provider_response: Full provider response

        Returns:
            Assertion result dictionary
        """
        assertion_func = assertion_registry.get_assertion(assertion.type)
        if not assertion_func:
            raise EvaluationError(f"Unknown assertion type: {assertion.type}")

        try:
            result = await assertion_func(assertion, response_text, provider_response)
            return {
                "type": assertion.type,
                "passed": result.get("passed", False),
                "score": result.get("score"),
                "message": result.get("message"),
                "metadata": result.get("metadata", {}),
            }
        except Exception as e:
            return {
                "type": assertion.type,
                "passed": False,
                "error": str(e),
            }

    async def validate_providers(self) -> Dict[str, bool]:
        """Validate all configured providers.

        Returns:
            Dictionary mapping provider IDs to validation status
        """
        validation_results = {}
        
        for provider_id, provider in self.providers.items():
            try:
                await provider.validate_config()
                validation_results[provider_id] = True
            except Exception:
                validation_results[provider_id] = False

        return validation_results

    def get_provider_count(self) -> int:
        """Get the number of configured providers.

        Returns:
            Number of providers
        """
        return len(self.providers)

    def get_test_count(self) -> int:
        """Get the total number of tests to run.

        Returns:
            Total number of tests (prompts × providers × test cases)
        """
        return len(self.config.prompts) * len(self.providers) * len(self.config.tests)