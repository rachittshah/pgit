"""
Custom evaluators using JavaScript and Python for advanced assertions.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict

from ...config.models import Assertion


async def assert_javascript(
    assertion: Assertion, response_text: str, provider_response: Any
) -> Dict[str, Any]:
    """Execute JavaScript code to evaluate response.

    Args:
        assertion: Assertion configuration with JavaScript code
        response_text: Response text to evaluate
        provider_response: Full provider response

    Returns:
        Assertion result
    """
    if not assertion.value:
        return {
            "passed": False,
            "message": "JavaScript assertion requires code in the value field",
        }

    javascript_code = str(assertion.value)

    try:
        # Create evaluation context
        context = {
            "output": response_text,
            "response": {
                "content": response_text,
                "cost": getattr(provider_response, 'cost', None),
                "latency": getattr(provider_response, 'latency', None),
                "token_usage": getattr(provider_response, 'token_usage', None),
                "model": getattr(provider_response, 'model', None),
                "provider": getattr(provider_response, 'provider', None),
            }
        }

        # Wrap JavaScript code in evaluation function
        wrapped_code = f"""
const context = {json.dumps(context)};
const output = context.output;
const response = context.response;

// User's evaluation code
const result = (function() {{
    {javascript_code}
}})();

// Ensure result is a number (0-1) or boolean
let finalResult;
if (typeof result === 'boolean') {{
    finalResult = result ? 1 : 0;
}} else if (typeof result === 'number') {{
    finalResult = Math.max(0, Math.min(1, result));
}} else {{
    throw new Error('JavaScript evaluator must return a boolean or number between 0 and 1');
}}

console.log(JSON.stringify({{
    score: finalResult,
    passed: finalResult >= 0.5
}}));
"""

        # Execute JavaScript code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(wrapped_code)
            temp_file = f.name

        try:
            result = subprocess.run(
                ['node', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return {
                    "passed": False,
                    "message": f"JavaScript execution error: {result.stderr}",
                    "metadata": {
                        "javascript_code": javascript_code,
                        "error": result.stderr,
                    },
                }

            # Parse result
            output_data = json.loads(result.stdout.strip())
            score = output_data.get('score', 0)
            passed = output_data.get('passed', False)

            return {
                "passed": passed,
                "score": score,
                "message": f"JavaScript evaluation: {score:.2f}",
                "metadata": {
                    "javascript_code": javascript_code,
                    "evaluation_score": score,
                },
            }

        finally:
            Path(temp_file).unlink()

    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "message": "JavaScript evaluation timed out",
            "metadata": {"javascript_code": javascript_code},
        }

    except FileNotFoundError:
        return {
            "passed": False,
            "message": "Node.js not found. Please install Node.js to use JavaScript evaluators.",
            "metadata": {"javascript_code": javascript_code},
        }

    except json.JSONDecodeError as e:
        return {
            "passed": False,
            "message": f"JavaScript evaluation returned invalid JSON: {e}",
            "metadata": {"javascript_code": javascript_code},
        }

    except Exception as e:
        return {
            "passed": False,
            "message": f"JavaScript evaluation failed: {e}",
            "metadata": {"javascript_code": javascript_code},
        }


async def assert_python(
    assertion: Assertion, response_text: str, provider_response: Any
) -> Dict[str, Any]:
    """Execute Python code to evaluate response.

    Args:
        assertion: Assertion configuration with Python code
        response_text: Response text to evaluate
        provider_response: Full provider response

    Returns:
        Assertion result
    """
    if not assertion.value:
        return {
            "passed": False,
            "message": "Python assertion requires code in the value field",
        }

    python_code = str(assertion.value)

    try:
        # Create evaluation context
        context = {
            "output": response_text,
            "response": {
                "content": response_text,
                "cost": getattr(provider_response, 'cost', None),
                "latency": getattr(provider_response, 'latency', None),
                "token_usage": getattr(provider_response, 'token_usage', None),
                "model": getattr(provider_response, 'model', None),
                "provider": getattr(provider_response, 'provider', None),
            }
        }

        # Create safe execution environment
        safe_globals = {
            "__builtins__": {
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "min": min,
                "max": max,
                "sum": sum,
                "abs": abs,
                "round": round,
                "sorted": sorted,
                "reversed": reversed,
                "any": any,
                "all": all,
                "isinstance": isinstance,
                "type": type,
                "print": print,
            },
            "re": __import__("re"),
            "json": __import__("json"),
            "math": __import__("math"),
            "datetime": __import__("datetime"),
        }

        # Add context variables
        local_vars = context.copy()
        local_vars.update({
            "output": response_text,
            "response": context["response"],
        })

        # Execute Python code
        exec(python_code, safe_globals, local_vars)

        # Get result
        if "result" in local_vars:
            result = local_vars["result"]
        elif "score" in local_vars:
            result = local_vars["score"]
        else:
            return {
                "passed": False,
                "message": "Python evaluator must set 'result' or 'score' variable",
                "metadata": {"python_code": python_code},
            }

        # Convert result to score and passed status
        if isinstance(result, bool):
            score = 1.0 if result else 0.0
            passed = result
        elif isinstance(result, (int, float)):
            score = max(0, min(1, float(result)))
            passed = score >= 0.5
        else:
            return {
                "passed": False,
                "message": "Python evaluator result must be a boolean or number between 0 and 1",
                "metadata": {"python_code": python_code, "result_type": type(result).__name__},
            }

        return {
            "passed": passed,
            "score": score,
            "message": f"Python evaluation: {score:.2f}",
            "metadata": {
                "python_code": python_code,
                "evaluation_score": score,
                "local_variables": {k: v for k, v in local_vars.items() 
                                 if not k.startswith('_') and k not in context},
            },
        }

    except Exception as e:
        return {
            "passed": False,
            "message": f"Python evaluation failed: {e}",
            "metadata": {
                "python_code": python_code,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        }


async def assert_python_file(
    assertion: Assertion, response_text: str, provider_response: Any
) -> Dict[str, Any]:
    """Execute Python file to evaluate response.

    Args:
        assertion: Assertion configuration with Python file path
        response_text: Response text to evaluate
        provider_response: Full provider response

    Returns:
        Assertion result
    """
    if not assertion.value:
        return {
            "passed": False,
            "message": "Python file assertion requires file path in the value field",
        }

    file_path = str(assertion.value)
    script_path = Path(file_path)

    if not script_path.exists():
        return {
            "passed": False,
            "message": f"Python file not found: {file_path}",
        }

    try:
        # Create evaluation context
        context = {
            "output": response_text,
            "response": {
                "content": response_text,
                "cost": getattr(provider_response, 'cost', None),
                "latency": getattr(provider_response, 'latency', None),
                "token_usage": getattr(provider_response, 'token_usage', None),
                "model": getattr(provider_response, 'model', None),
                "provider": getattr(provider_response, 'provider', None),
            }
        }

        # Execute Python script as subprocess
        result = subprocess.run(
            ['python', str(script_path)],
            input=json.dumps(context),
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return {
                "passed": False,
                "message": f"Python script execution error: {result.stderr}",
                "metadata": {
                    "python_file": file_path,
                    "error": result.stderr,
                },
            }

        # Parse result
        try:
            output_data = json.loads(result.stdout.strip())
            
            if isinstance(output_data, dict):
                score = output_data.get('score', output_data.get('result', 0))
                passed = output_data.get('passed', score >= 0.5)
                message = output_data.get('message', f"Python file evaluation: {score:.2f}")
                
                return {
                    "passed": passed,
                    "score": score,
                    "message": message,
                    "metadata": {
                        "python_file": file_path,
                        "evaluation_score": score,
                        "script_output": output_data,
                    },
                }
            else:
                # Treat as raw score
                score = max(0, min(1, float(output_data)))
                return {
                    "passed": score >= 0.5,
                    "score": score,
                    "message": f"Python file evaluation: {score:.2f}",
                    "metadata": {
                        "python_file": file_path,
                        "evaluation_score": score,
                    },
                }

        except (json.JSONDecodeError, ValueError):
            # Raw text output
            output_text = result.stdout.strip()
            return {
                "passed": False,
                "message": f"Python script returned non-numeric result: {output_text}",
                "metadata": {
                    "python_file": file_path,
                    "raw_output": output_text,
                },
            }

    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "message": "Python script execution timed out",
            "metadata": {"python_file": file_path},
        }

    except Exception as e:
        return {
            "passed": False,
            "message": f"Python file evaluation failed: {e}",
            "metadata": {
                "python_file": file_path,
                "error": str(e),
            },
        }