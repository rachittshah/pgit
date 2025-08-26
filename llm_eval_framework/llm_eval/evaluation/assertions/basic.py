"""
Basic assertion functions for promptfoo-python.
"""

import re
from typing import Any, Dict

from ...config.models import Assertion


async def assert_contains(
    assertion: Assertion, response_text: str, provider_response: Any
) -> Dict[str, Any]:
    """Check if response contains specified text.

    Args:
        assertion: Assertion configuration
        response_text: Response text to check
        provider_response: Full provider response

    Returns:
        Assertion result
    """
    expected = str(assertion.value) if assertion.value is not None else ""
    contains = expected in response_text

    return {
        "passed": contains,
        "message": f"Expected response to contain '{expected}'" + 
                  ("" if contains else f", but got: '{response_text[:100]}...'"),
        "metadata": {
            "expected": expected,
            "actual": response_text,
            "found": contains,
        },
    }


async def assert_not_contains(
    assertion: Assertion, response_text: str, provider_response: Any
) -> Dict[str, Any]:
    """Check if response does not contain specified text.

    Args:
        assertion: Assertion configuration
        response_text: Response text to check
        provider_response: Full provider response

    Returns:
        Assertion result
    """
    unexpected = str(assertion.value) if assertion.value is not None else ""
    not_contains = unexpected not in response_text

    return {
        "passed": not_contains,
        "message": f"Expected response to not contain '{unexpected}'" + 
                  ("" if not_contains else f", but found it in: '{response_text[:100]}...'"),
        "metadata": {
            "unexpected": unexpected,
            "actual": response_text,
            "found": not not_contains,
        },
    }


async def assert_icontains(
    assertion: Assertion, response_text: str, provider_response: Any
) -> Dict[str, Any]:
    """Check if response contains specified text (case insensitive).

    Args:
        assertion: Assertion configuration
        response_text: Response text to check
        provider_response: Full provider response

    Returns:
        Assertion result
    """
    expected = str(assertion.value) if assertion.value is not None else ""
    contains = expected.lower() in response_text.lower()

    return {
        "passed": contains,
        "message": f"Expected response to contain '{expected}' (case insensitive)" + 
                  ("" if contains else f", but got: '{response_text[:100]}...'"),
        "metadata": {
            "expected": expected,
            "actual": response_text,
            "found": contains,
        },
    }


async def assert_cost(
    assertion: Assertion, response_text: str, provider_response: Any
) -> Dict[str, Any]:
    """Check if response cost is below threshold.

    Args:
        assertion: Assertion configuration
        response_text: Response text to check
        provider_response: Full provider response

    Returns:
        Assertion result
    """
    threshold = assertion.threshold
    if threshold is None:
        return {
            "passed": False,
            "message": "Cost assertion requires a threshold value",
        }

    # Get cost from provider response
    actual_cost = getattr(provider_response, 'cost', None)
    if actual_cost is None:
        return {
            "passed": False,
            "message": "Cost information not available from provider",
            "metadata": {
                "threshold": threshold,
            },
        }

    passed = actual_cost <= threshold

    return {
        "passed": passed,
        "message": f"Expected cost ≤ ${threshold:.4f}, got ${actual_cost:.4f}",
        "metadata": {
            "threshold": threshold,
            "actual_cost": actual_cost,
            "savings": threshold - actual_cost if passed else None,
        },
    }


async def assert_latency(
    assertion: Assertion, response_text: str, provider_response: Any
) -> Dict[str, Any]:
    """Check if response latency is below threshold.

    Args:
        assertion: Assertion configuration
        response_text: Response text to check
        provider_response: Full provider response

    Returns:
        Assertion result
    """
    threshold = assertion.threshold
    if threshold is None:
        return {
            "passed": False,
            "message": "Latency assertion requires a threshold value (in seconds)",
        }

    # Get latency from provider response
    actual_latency = getattr(provider_response, 'latency', None)
    if actual_latency is None:
        return {
            "passed": False,
            "message": "Latency information not available from provider",
            "metadata": {
                "threshold": threshold,
            },
        }

    passed = actual_latency <= threshold

    return {
        "passed": passed,
        "message": f"Expected latency ≤ {threshold:.2f}s, got {actual_latency:.2f}s",
        "metadata": {
            "threshold": threshold,
            "actual_latency": actual_latency,
            "margin": threshold - actual_latency if passed else None,
        },
    }


async def assert_regex(
    assertion: Assertion, response_text: str, provider_response: Any
) -> Dict[str, Any]:
    """Check if response matches a regular expression.

    Args:
        assertion: Assertion configuration
        response_text: Response text to check
        provider_response: Full provider response

    Returns:
        Assertion result
    """
    pattern = str(assertion.value) if assertion.value is not None else ""
    if not pattern:
        return {
            "passed": False,
            "message": "Regex assertion requires a pattern value",
        }

    try:
        match = re.search(pattern, response_text, re.MULTILINE | re.DOTALL)
        passed = match is not None

        return {
            "passed": passed,
            "message": f"Expected response to match regex pattern '{pattern}'" + 
                      ("" if passed else f", but got: '{response_text[:100]}...'"),
            "metadata": {
                "pattern": pattern,
                "actual": response_text,
                "match": match.group() if match else None,
                "match_groups": match.groups() if match else None,
            },
        }

    except re.error as e:
        return {
            "passed": False,
            "message": f"Invalid regex pattern '{pattern}': {e}",
            "metadata": {
                "pattern": pattern,
                "error": str(e),
            },
        }


async def assert_tool_called(
    assertion: Assertion, response_text: str, provider_response: Any
) -> Dict[str, Any]:
    """Check if a specific tool was called.

    Args:
        assertion: Assertion configuration
        response_text: Response text to check
        provider_response: Full provider response

    Returns:
        Assertion result
    """
    expected_tool = str(assertion.value) if assertion.value is not None else ""
    if not expected_tool:
        return {
            "passed": False,
            "message": "Tool-called assertion requires a tool name value",
        }

    # Get tool calls from provider response
    tool_calls = getattr(provider_response, 'tool_calls', None)
    if not tool_calls:
        return {
            "passed": False,
            "message": f"Expected tool '{expected_tool}' to be called, but no tools were called",
            "metadata": {
                "expected_tool": expected_tool,
                "called_tools": [],
            },
        }

    # Check if the expected tool was called
    called_tools = [tc.name for tc in tool_calls]
    passed = expected_tool in called_tools

    return {
        "passed": passed,
        "message": f"Expected tool '{expected_tool}' to be called" + 
                  ("" if passed else f", but only called: {called_tools}"),
        "metadata": {
            "expected_tool": expected_tool,
            "called_tools": called_tools,
            "tool_calls": [{"name": tc.name, "arguments": tc.arguments} for tc in tool_calls],
        },
    }


async def assert_json_schema(
    assertion: Assertion, response_text: str, provider_response: Any
) -> Dict[str, Any]:
    """Check if response is valid JSON matching a schema.

    Args:
        assertion: Assertion configuration
        response_text: Response text to check
        provider_response: Full provider response

    Returns:
        Assertion result
    """
    import json
    
    try:
        # Try to parse as JSON
        parsed_json = json.loads(response_text)
        
        # If no schema provided, just check if it's valid JSON
        if assertion.value is None:
            return {
                "passed": True,
                "message": "Response is valid JSON",
                "metadata": {
                    "parsed_json": parsed_json,
                },
            }

        # TODO: Implement JSON schema validation with jsonschema library
        # For now, just return success if JSON is valid
        return {
            "passed": True,
            "message": "Response is valid JSON (schema validation not yet implemented)",
            "metadata": {
                "parsed_json": parsed_json,
                "schema": assertion.value,
            },
        }

    except json.JSONDecodeError as e:
        return {
            "passed": False,
            "message": f"Response is not valid JSON: {e}",
            "metadata": {
                "error": str(e),
                "response_text": response_text[:100] + "..." if len(response_text) > 100 else response_text,
            },
        }