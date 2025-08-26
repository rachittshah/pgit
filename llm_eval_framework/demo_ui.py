#!/usr/bin/env python3
"""
Demo script to populate the web UI with sample evaluation results.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

# Import the web app and models
from llm_eval.web.app import update_current_results
from llm_eval.config.models import EvaluationSummary, EvaluationResult, LLMEvalConfig


def create_sample_results():
    """Create sample evaluation results for demonstration."""
    
    # Sample test results
    results = []
    
    # GPT-4 results
    gpt4_results = [
        EvaluationResult(
            provider_id="gpt-4",
            prompt="What is the capital of France?",
            response="The capital of France is Paris. Paris is located in the north-central part of France and has been the country's capital since 508 CE.",
            success=True,
            cost=0.0012,
            latency=1.2,
            assertion_results=[
                {"type": "contains", "passed": True, "message": "Contains 'Paris'", "score": 1.0},
                {"type": "not-contains", "passed": True, "message": "Does not contain 'London'", "score": 1.0}
            ],
            vars={"question": "What is the capital of France?"}
        ),
        EvaluationResult(
            provider_id="gpt-4",
            prompt="Explain machine learning in simple terms",
            response="Machine learning is a way for computers to learn patterns from data without being explicitly programmed for every scenario. It's like teaching a computer to recognize patterns by showing it many examples.",
            success=True,
            cost=0.0018,
            latency=2.1,
            assertion_results=[
                {"type": "contains", "passed": True, "message": "Contains 'learning'", "score": 1.0},
                {"type": "llm-rubric", "passed": True, "score": 0.88, "message": "Good explanation quality"}
            ],
            vars={"question": "Explain machine learning"}
        )
    ]
    
    # GPT-3.5-turbo results
    gpt35_results = [
        EvaluationResult(
            provider_id="gpt-3.5-turbo",
            prompt="What is the capital of France?",
            response="Paris is the capital of France.",
            success=True,
            cost=0.0003,
            latency=0.8,
            assertion_results=[
                {"type": "contains", "passed": True, "message": "Contains 'Paris'", "score": 1.0},
                {"type": "not-contains", "passed": True, "message": "Does not contain 'London'", "score": 1.0}
            ],
            vars={"question": "What is the capital of France?"}
        ),
        EvaluationResult(
            provider_id="gpt-3.5-turbo",
            prompt="Explain machine learning in simple terms",
            response="Machine learning is when computers learn from data to make predictions or decisions without being explicitly programmed.",
            success=True,
            cost=0.0005,
            latency=1.3,
            assertion_results=[
                {"type": "contains", "passed": True, "message": "Contains 'learning'", "score": 1.0},
                {"type": "llm-rubric", "passed": True, "score": 0.75, "message": "Adequate explanation"}
            ],
            vars={"question": "Explain machine learning"}
        )
    ]
    
    # Claude results
    claude_results = [
        EvaluationResult(
            provider_id="claude-3-sonnet",
            prompt="What is the capital of France?",
            response="The capital city of France is Paris. It's located in the Île-de-France region and serves as the political, economic, and cultural center of the country.",
            success=True,
            cost=0.0015,
            latency=1.5,
            assertion_results=[
                {"type": "contains", "passed": True, "message": "Contains 'Paris'", "score": 1.0},
                {"type": "not-contains", "passed": True, "message": "Does not contain 'London'", "score": 1.0}
            ],
            vars={"question": "What is the capital of France?"}
        ),
        EvaluationResult(
            provider_id="claude-3-sonnet",
            prompt="Explain machine learning in simple terms",
            response="Machine learning is a subset of artificial intelligence where computers learn to make predictions or decisions by finding patterns in data, rather than following pre-written rules. Think of it like teaching a computer to recognize cats in photos by showing it thousands of cat pictures.",
            success=True,
            cost=0.0020,
            latency=1.8,
            assertion_results=[
                {"type": "contains", "passed": True, "message": "Contains 'learning'", "score": 1.0},
                {"type": "llm-rubric", "passed": True, "score": 0.93, "message": "Excellent explanation with examples"}
            ],
            vars={"question": "Explain machine learning"}
        )
    ]
    
    # Add one failed test for demonstration
    failed_result = EvaluationResult(
        provider_id="gpt-3.5-turbo",
        prompt="What is 2+2?",
        response="The answer is 5.",
        success=False,
        cost=0.0002,
        latency=0.6,
        assertion_results=[
            {"type": "contains", "passed": False, "message": "Should contain '4'", "score": 0.0}
        ],
        error="Assertion failed: Response should contain '4'",
        vars={"question": "What is 2+2?"}
    )
    
    # Combine all results
    all_results = gpt4_results + gpt35_results + claude_results + [failed_result]
    
    # Calculate summary statistics
    total_tests = len(all_results)
    passed_tests = sum(1 for r in all_results if r.success)
    failed_tests = total_tests - passed_tests
    total_cost = sum(r.cost for r in all_results if r.cost)
    average_latency = sum(r.latency for r in all_results if r.latency) / total_tests
    
    # Create a sample config
    config = LLMEvalConfig(
        description="Demo LLM Evaluation Results",
        providers=["gpt-4", "gpt-3.5-turbo", "claude-3-sonnet"],
        prompts=["What is {{question}}?", "Explain {{topic}} in simple terms"]
    )
    
    # Create evaluation summary
    summary = EvaluationSummary(
        config=config,
        results=all_results,
        total_tests=total_tests,
        passed_tests=passed_tests,
        failed_tests=failed_tests,
        total_cost=total_cost,
        average_latency=average_latency,
        timestamp=datetime.now().isoformat()
    )
    
    return summary


def load_sample_data():
    """Load sample data into the web dashboard."""
    print("🚀 Loading sample evaluation results into the web dashboard...")
    
    # Create sample results
    summary = create_sample_results()
    
    # Update the dashboard
    update_current_results(summary)
    
    # Calculate pass rate and average score from assertion results
    total_assertions = sum(len(r.assertion_results) for r in summary.results)
    passed_assertions = sum(
        len([a for a in r.assertion_results if a.get("passed", False)]) 
        for r in summary.results
    )
    pass_rate = passed_assertions / total_assertions if total_assertions > 0 else 0
    
    # Calculate average score from assertion results
    all_scores = []
    for result in summary.results:
        for assertion in result.assertion_results:
            if "score" in assertion:
                all_scores.append(assertion["score"])
    average_score = sum(all_scores) / len(all_scores) if all_scores else 0
    
    print(f"✅ Loaded {summary.total_tests} test results:")
    print(f"   • {summary.passed_tests} passed, {summary.failed_tests} failed")
    print(f"   • Pass rate: {pass_rate:.1%}")
    print(f"   • Average score: {average_score:.3f}")
    print(f"   • Total cost: ${summary.total_cost:.4f}")
    print(f"   • Average latency: {summary.average_latency:.1f}s")
    print()
    print("🌐 Dashboard is now populated with sample data!")
    print("   Visit: http://localhost:8081")
    print()
    print("📊 Available features:")
    print("   • View evaluation results and metrics")
    print("   • Compare provider performance") 
    print("   • Export results to JSON/CSV")
    print("   • Share results with shareable links")
    print("   • Give thumbs up/down feedback")
    print()
    print("🔗 Try these API endpoints:")
    print("   • GET  /api/results - Get current results")
    print("   • GET  /api/compare - Provider comparison data")
    print("   • POST /api/share - Create shareable link")
    print("   • POST /api/export/json - Export as JSON")
    print("   • POST /api/export/csv - Export as CSV")


if __name__ == "__main__":
    load_sample_data()