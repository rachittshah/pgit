"""
Streaming evaluation support for real-time LLM response processing.
"""

import asyncio
import time
from typing import Any, AsyncGenerator, Dict, List, Optional

from ..config.models import TestCase, Assertion, EvaluationResult
from ..providers.base import BaseProvider, Message, ProviderResponse
from .assertions.registry import assertion_registry


class StreamingEvaluator:
    """Evaluator with streaming support for real-time response processing."""

    def __init__(self, providers: Dict[str, BaseProvider]):
        """Initialize streaming evaluator.

        Args:
            providers: Dictionary of provider instances
        """
        self.providers = providers

    async def stream_evaluation(
        self, 
        prompt_template: str,
        test_case: TestCase,
        provider_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream evaluation results in real-time.

        Args:
            prompt_template: Prompt template
            test_case: Test case to evaluate
            provider_id: Provider to use

        Yields:
            Streaming evaluation updates
        """
        if provider_id not in self.providers:
            yield {
                "type": "error",
                "message": f"Provider {provider_id} not found",
                "timestamp": time.time()
            }
            return

        provider = self.providers[provider_id]

        try:
            # Yield start event
            yield {
                "type": "start",
                "provider_id": provider_id,
                "prompt": prompt_template,
                "timestamp": time.time()
            }

            # Render prompt
            from jinja2 import Template
            template = Template(prompt_template)
            rendered_prompt = template.render(**(test_case.vars or {}))

            yield {
                "type": "prompt_rendered",
                "rendered_prompt": rendered_prompt,
                "timestamp": time.time()
            }

            # Stream response generation
            start_time = time.time()
            
            # For now, we'll simulate streaming by chunking the response
            # In future versions, integrate with LiteLLM's streaming capabilities
            response = await provider.generate_text(rendered_prompt)
            
            # Simulate streaming by yielding chunks
            full_response = response.content
            chunk_size = 20  # Characters per chunk
            
            accumulated_response = ""
            for i in range(0, len(full_response), chunk_size):
                chunk = full_response[i:i + chunk_size]
                accumulated_response += chunk
                
                yield {
                    "type": "response_chunk",
                    "chunk": chunk,
                    "accumulated_response": accumulated_response,
                    "timestamp": time.time()
                }
                
                # Small delay to simulate real streaming
                await asyncio.sleep(0.1)

            # Calculate final metrics
            latency = time.time() - start_time

            yield {
                "type": "response_complete",
                "full_response": full_response,
                "latency": latency,
                "cost": response.cost,
                "token_usage": response.token_usage,
                "timestamp": time.time()
            }

            # Run assertions in real-time
            if test_case.assert_:
                yield {
                    "type": "assertions_start",
                    "total_assertions": len(test_case.assert_),
                    "timestamp": time.time()
                }

                assertion_results = []
                for i, assertion in enumerate(test_case.assert_):
                    yield {
                        "type": "assertion_start",
                        "assertion_index": i,
                        "assertion_type": assertion.type,
                        "timestamp": time.time()
                    }

                    try:
                        assertion_result = await self._run_assertion(
                            assertion, full_response, response
                        )
                        assertion_results.append(assertion_result)

                        yield {
                            "type": "assertion_complete",
                            "assertion_index": i,
                            "assertion_type": assertion.type,
                            "result": assertion_result,
                            "timestamp": time.time()
                        }

                    except Exception as e:
                        assertion_result = {
                            "type": assertion.type,
                            "passed": False,
                            "error": str(e),
                        }
                        assertion_results.append(assertion_result)

                        yield {
                            "type": "assertion_error",
                            "assertion_index": i,
                            "assertion_type": assertion.type,
                            "error": str(e),
                            "timestamp": time.time()
                        }

            # Final evaluation result
            overall_success = all(
                result.get("passed", False) for result in assertion_results
            )

            final_result = EvaluationResult(
                provider_id=provider_id,
                prompt=rendered_prompt,
                vars=test_case.vars or {},
                response=full_response,
                cost=response.cost,
                latency=latency,
                assertion_results=assertion_results,
                success=overall_success,
                metadata={
                    "model": response.model,
                    "provider": response.provider,
                    "token_usage": response.token_usage,
                    "finish_reason": response.finish_reason,
                },
            )

            yield {
                "type": "evaluation_complete",
                "result": final_result.dict(),
                "timestamp": time.time()
            }

        except Exception as e:
            yield {
                "type": "error",
                "message": str(e),
                "timestamp": time.time()
            }

    async def stream_comparison(
        self,
        prompt_template: str,
        test_case: TestCase,
        provider_ids: List[str]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream comparison across multiple providers simultaneously.

        Args:
            prompt_template: Prompt template
            test_case: Test case to evaluate
            provider_ids: List of providers to compare

        Yields:
            Streaming comparison updates
        """
        yield {
            "type": "comparison_start",
            "providers": provider_ids,
            "timestamp": time.time()
        }

        # Start streaming evaluations for all providers
        streaming_tasks = []
        for provider_id in provider_ids:
            if provider_id in self.providers:
                task = asyncio.create_task(
                    self._collect_streaming_result(
                        prompt_template, test_case, provider_id
                    )
                )
                streaming_tasks.append((provider_id, task))

        # Yield results as they complete
        completed = 0
        while completed < len(streaming_tasks):
            for provider_id, task in streaming_tasks:
                if task.done() and not hasattr(task, "_yielded"):
                    try:
                        result = await task
                        yield {
                            "type": "provider_complete",
                            "provider_id": provider_id,
                            "result": result,
                            "timestamp": time.time()
                        }
                        task._yielded = True
                        completed += 1
                    except Exception as e:
                        yield {
                            "type": "provider_error",
                            "provider_id": provider_id,
                            "error": str(e),
                            "timestamp": time.time()
                        }
                        task._yielded = True
                        completed += 1

            await asyncio.sleep(0.1)

        yield {
            "type": "comparison_complete",
            "timestamp": time.time()
        }

    async def _collect_streaming_result(
        self,
        prompt_template: str,
        test_case: TestCase,
        provider_id: str
    ) -> Dict[str, Any]:
        """Collect streaming result for a single provider.

        Args:
            prompt_template: Prompt template
            test_case: Test case
            provider_id: Provider ID

        Returns:
            Complete evaluation result
        """
        result = None
        async for update in self.stream_evaluation(prompt_template, test_case, provider_id):
            if update["type"] == "evaluation_complete":
                result = update["result"]
                break

        return result or {"error": "No result received"}

    async def _run_assertion(
        self, 
        assertion: Assertion, 
        response_text: str, 
        provider_response: Any
    ) -> Dict[str, Any]:
        """Run a single assertion (same as base evaluator)."""
        assertion_func = assertion_registry.get_assertion(assertion.type)
        if not assertion_func:
            raise ValueError(f"Unknown assertion type: {assertion.type}")

        return await assertion_func(assertion, response_text, provider_response)