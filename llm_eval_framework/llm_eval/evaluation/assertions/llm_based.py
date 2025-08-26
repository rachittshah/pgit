"""
LLM-based assertion functions using other models as judges.
"""

from typing import Any, Dict, Optional

from ...config.models import Assertion
from ...providers.registry import create_provider


async def assert_llm_rubric(
    assertion: Assertion, response_text: str, provider_response: Any
) -> Dict[str, Any]:
    """Use an LLM to grade the response based on a rubric.

    Args:
        assertion: Assertion configuration with rubric
        response_text: Response text to evaluate
        provider_response: Full provider response

    Returns:
        Assertion result with LLM grading
    """
    if not assertion.value:
        return {
            "passed": False,
            "message": "LLM rubric assertion requires a rubric prompt in the value field",
        }

    rubric = str(assertion.value)
    
    try:
        # Create a judge LLM (use GPT-3.5 for speed and cost efficiency)
        judge_provider = create_provider("openai/gpt-3.5-turbo")
        
        # Create evaluation prompt
        eval_prompt = f"""
You are an expert evaluator. Please evaluate the following AI response based on the given rubric.

RUBRIC:
{rubric}

AI RESPONSE TO EVALUATE:
{response_text}

Please respond with:
1. SCORE: A number from 0 to 100
2. PASSED: YES or NO (based on whether this meets the rubric criteria)
3. FEEDBACK: Brief explanation of your evaluation

Format your response as:
SCORE: [number]
PASSED: [YES/NO]
FEEDBACK: [explanation]
"""

        # Get LLM evaluation
        judge_response = await judge_provider.generate_text(
            eval_prompt, 
            temperature=0.1  # Low temperature for consistent grading
        )
        
        # Parse the response
        evaluation = _parse_llm_evaluation(judge_response.content)
        
        return {
            "passed": evaluation["passed"],
            "score": evaluation["score"] / 100.0,  # Normalize to 0-1
            "message": evaluation["feedback"],
            "metadata": {
                "judge_model": "openai/gpt-3.5-turbo",
                "rubric": rubric,
                "raw_evaluation": judge_response.content,
                "judge_cost": judge_response.cost,
            },
        }

    except Exception as e:
        return {
            "passed": False,
            "message": f"LLM rubric evaluation failed: {e}",
            "metadata": {
                "error": str(e),
                "rubric": rubric,
            },
        }


async def assert_llm_factcheck(
    assertion: Assertion, response_text: str, provider_response: Any
) -> Dict[str, Any]:
    """Use an LLM to fact-check the response.

    Args:
        assertion: Assertion configuration
        response_text: Response text to check
        provider_response: Full provider response

    Returns:
        Assertion result with fact-checking
    """
    try:
        # Create a judge LLM
        judge_provider = create_provider("openai/gpt-4o-mini")  # Better for factual accuracy
        
        # Create fact-checking prompt
        factcheck_prompt = f"""
You are a fact-checking expert. Please evaluate the factual accuracy of the following statement.

STATEMENT TO FACT-CHECK:
{response_text}

Please respond with:
1. ACCURACY: A rating from 0-100 (0 = completely false, 100 = completely accurate)
2. VERDICT: ACCURATE, PARTIALLY_ACCURATE, or INACCURATE
3. ISSUES: List any factual errors or concerns (or "None" if accurate)

Format your response as:
ACCURACY: [number]
VERDICT: [ACCURATE/PARTIALLY_ACCURATE/INACCURATE]
ISSUES: [list of issues or "None"]
"""

        # Get LLM fact-check
        judge_response = await judge_provider.generate_text(
            factcheck_prompt,
            temperature=0.0  # Very low temperature for factual consistency
        )
        
        # Parse the response
        factcheck = _parse_factcheck_response(judge_response.content)
        
        # Consider it passed if accuracy >= 80 and verdict is not INACCURATE
        passed = factcheck["accuracy"] >= 80 and factcheck["verdict"] != "INACCURATE"
        
        return {
            "passed": passed,
            "score": factcheck["accuracy"] / 100.0,
            "message": f"Factual accuracy: {factcheck['accuracy']}%. Verdict: {factcheck['verdict']}",
            "metadata": {
                "judge_model": "openai/gpt-4o-mini",
                "accuracy_score": factcheck["accuracy"],
                "verdict": factcheck["verdict"],
                "issues": factcheck["issues"],
                "raw_evaluation": judge_response.content,
                "judge_cost": judge_response.cost,
            },
        }

    except Exception as e:
        return {
            "passed": False,
            "message": f"LLM fact-check failed: {e}",
            "metadata": {
                "error": str(e),
            },
        }


async def assert_llm_helpfulness(
    assertion: Assertion, response_text: str, provider_response: Any
) -> Dict[str, Any]:
    """Use an LLM to evaluate the helpfulness of the response.

    Args:
        assertion: Assertion configuration
        response_text: Response text to evaluate  
        provider_response: Full provider response

    Returns:
        Assertion result with helpfulness evaluation
    """
    try:
        # Create a judge LLM
        judge_provider = create_provider("openai/gpt-3.5-turbo")
        
        # Create helpfulness evaluation prompt
        helpfulness_prompt = f"""
You are evaluating the helpfulness of an AI response. Consider how useful, relevant, and actionable the response is.

AI RESPONSE TO EVALUATE:
{response_text}

Please rate the response on these criteria:
1. RELEVANCE: Does it address the question/request?
2. COMPLETENESS: Is the answer comprehensive?
3. CLARITY: Is it easy to understand?
4. ACTIONABILITY: Can the user act on this information?

Provide:
HELPFULNESS_SCORE: A number from 0-100
PASSED: YES or NO (score >= 70 is considered helpful)
REASONING: Brief explanation of your rating

Format:
HELPFULNESS_SCORE: [number]
PASSED: [YES/NO]
REASONING: [explanation]
"""

        # Get LLM evaluation
        judge_response = await judge_provider.generate_text(
            helpfulness_prompt,
            temperature=0.2
        )
        
        # Parse the response
        evaluation = _parse_helpfulness_response(judge_response.content)
        
        return {
            "passed": evaluation["passed"],
            "score": evaluation["score"] / 100.0,
            "message": f"Helpfulness score: {evaluation['score']}%. {evaluation['reasoning']}",
            "metadata": {
                "judge_model": "openai/gpt-3.5-turbo",
                "helpfulness_score": evaluation["score"],
                "reasoning": evaluation["reasoning"],
                "raw_evaluation": judge_response.content,
                "judge_cost": judge_response.cost,
            },
        }

    except Exception as e:
        return {
            "passed": False,
            "message": f"LLM helpfulness evaluation failed: {e}",
            "metadata": {
                "error": str(e),
            },
        }


def _parse_llm_evaluation(response: str) -> Dict[str, Any]:
    """Parse LLM evaluation response.

    Args:
        response: Raw LLM response

    Returns:
        Parsed evaluation data
    """
    lines = response.strip().split('\n')
    evaluation = {
        "score": 0,
        "passed": False,
        "feedback": "Failed to parse evaluation"
    }
    
    for line in lines:
        line = line.strip()
        if line.startswith("SCORE:"):
            try:
                score_str = line.split(":", 1)[1].strip()
                evaluation["score"] = int(score_str)
            except (ValueError, IndexError):
                pass
        elif line.startswith("PASSED:"):
            try:
                passed_str = line.split(":", 1)[1].strip().upper()
                evaluation["passed"] = passed_str == "YES"
            except IndexError:
                pass
        elif line.startswith("FEEDBACK:"):
            try:
                evaluation["feedback"] = line.split(":", 1)[1].strip()
            except IndexError:
                pass
    
    return evaluation


def _parse_factcheck_response(response: str) -> Dict[str, Any]:
    """Parse fact-check response.

    Args:
        response: Raw LLM response

    Returns:
        Parsed fact-check data
    """
    lines = response.strip().split('\n')
    factcheck = {
        "accuracy": 0,
        "verdict": "UNKNOWN",
        "issues": "Failed to parse response"
    }
    
    for line in lines:
        line = line.strip()
        if line.startswith("ACCURACY:"):
            try:
                accuracy_str = line.split(":", 1)[1].strip()
                factcheck["accuracy"] = int(accuracy_str)
            except (ValueError, IndexError):
                pass
        elif line.startswith("VERDICT:"):
            try:
                factcheck["verdict"] = line.split(":", 1)[1].strip().upper()
            except IndexError:
                pass
        elif line.startswith("ISSUES:"):
            try:
                factcheck["issues"] = line.split(":", 1)[1].strip()
            except IndexError:
                pass
    
    return factcheck


def _parse_helpfulness_response(response: str) -> Dict[str, Any]:
    """Parse helpfulness evaluation response.

    Args:
        response: Raw LLM response

    Returns:
        Parsed helpfulness data
    """
    lines = response.strip().split('\n')
    evaluation = {
        "score": 0,
        "passed": False,
        "reasoning": "Failed to parse response"
    }
    
    for line in lines:
        line = line.strip()
        if line.startswith("HELPFULNESS_SCORE:"):
            try:
                score_str = line.split(":", 1)[1].strip()
                evaluation["score"] = int(score_str)
            except (ValueError, IndexError):
                pass
        elif line.startswith("PASSED:"):
            try:
                passed_str = line.split(":", 1)[1].strip().upper()
                evaluation["passed"] = passed_str == "YES"
            except IndexError:
                pass
        elif line.startswith("REASONING:"):
            try:
                evaluation["reasoning"] = line.split(":", 1)[1].strip()
            except IndexError:
                pass
    
    return evaluation