"""
Assertion registry for managing different assertion types.
"""

import re
from typing import Any, Callable, Dict, Optional

from ...config.models import Assertion


class AssertionRegistry:
    """Registry for assertion functions."""

    def __init__(self):
        """Initialize the assertion registry."""
        self._assertions: Dict[str, Callable] = {}
        self._register_default_assertions()

    def _register_default_assertions(self):
        """Register default assertion functions."""
        # Import and register basic assertions
        from .basic import (
            assert_contains,
            assert_not_contains,
            assert_icontains,
            assert_cost,
            assert_latency,
            assert_regex,
            assert_tool_called,
            assert_json_schema,
        )
        
        # Import and register LLM-based assertions
        from .llm_based import (
            assert_llm_rubric,
            assert_llm_factcheck,
            assert_llm_helpfulness,
        )
        
        # Import and register custom evaluators
        from .custom import (
            assert_javascript,
            assert_python,
            assert_python_file,
        )

        # Basic assertions
        self.register("contains", assert_contains)
        self.register("not-contains", assert_not_contains)
        self.register("icontains", assert_icontains)
        self.register("cost", assert_cost)
        self.register("latency", assert_latency)
        self.register("regex", assert_regex)
        self.register("tool-called", assert_tool_called)
        self.register("json-schema", assert_json_schema)
        
        # LLM-based assertions
        self.register("llm-rubric", assert_llm_rubric)
        self.register("llm-factcheck", assert_llm_factcheck)
        self.register("llm-helpfulness", assert_llm_helpfulness)
        
        # Custom evaluators
        self.register("javascript", assert_javascript)
        self.register("python", assert_python)
        self.register("python-file", assert_python_file)

    def register(self, assertion_type: str, assertion_func: Callable):
        """Register an assertion function.

        Args:
            assertion_type: Type name for the assertion
            assertion_func: Assertion function that takes (assertion, response_text, provider_response)
                           and returns a dict with 'passed' and optional 'message', 'score', 'metadata'
        """
        self._assertions[assertion_type] = assertion_func

    def get_assertion(self, assertion_type: str) -> Optional[Callable]:
        """Get assertion function by type.

        Args:
            assertion_type: Type name

        Returns:
            Assertion function or None if not found
        """
        return self._assertions.get(assertion_type)

    def list_assertions(self) -> Dict[str, Callable]:
        """List all registered assertions.

        Returns:
            Dictionary of assertion type to function mappings
        """
        return self._assertions.copy()

    def is_assertion_available(self, assertion_type: str) -> bool:
        """Check if an assertion type is available.

        Args:
            assertion_type: Type name

        Returns:
            True if assertion is available
        """
        return assertion_type in self._assertions


# Global assertion registry instance
assertion_registry = AssertionRegistry()


# Convenience functions
def register_assertion(assertion_type: str, assertion_func: Callable):
    """Register an assertion function globally.

    Args:
        assertion_type: Type name for the assertion
        assertion_func: Assertion function
    """
    assertion_registry.register(assertion_type, assertion_func)


def get_assertion(assertion_type: str) -> Optional[Callable]:
    """Get assertion function by type globally.

    Args:
        assertion_type: Type name

    Returns:
        Assertion function or None if not found
    """
    return assertion_registry.get_assertion(assertion_type)


def list_available_assertions() -> Dict[str, Callable]:
    """List all available assertion types globally.

    Returns:
        Dictionary of assertion type to function mappings
    """
    return assertion_registry.list_assertions()