"""
Advanced analytics and metrics calculation for LLM evaluation results.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import json


@dataclass
class EvaluationMetrics:
    """Container for evaluation metrics."""
    
    # Basic metrics
    total_tests: int
    passed_tests: int
    failed_tests: int
    pass_rate: float
    average_score: float
    
    # Performance metrics
    total_cost: float
    average_cost: float
    total_latency: float
    average_latency: float
    
    # Quality metrics
    score_distribution: Dict[str, int]
    assertion_pass_rates: Dict[str, float]
    
    # Provider metrics (if multiple providers)
    provider_stats: Dict[str, Dict[str, Any]]
    
    # Time-based metrics
    evaluation_duration: float
    throughput: float  # tests per second
    
    # Additional statistics
    score_std: float
    cost_std: float
    latency_std: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "basic_metrics": {
                "total_tests": self.total_tests,
                "passed_tests": self.passed_tests,
                "failed_tests": self.failed_tests,
                "pass_rate": self.pass_rate,
                "average_score": self.average_score
            },
            "performance_metrics": {
                "total_cost": self.total_cost,
                "average_cost": self.average_cost,
                "total_latency": self.total_latency,
                "average_latency": self.average_latency
            },
            "quality_metrics": {
                "score_distribution": self.score_distribution,
                "assertion_pass_rates": self.assertion_pass_rates
            },
            "provider_stats": self.provider_stats,
            "time_metrics": {
                "evaluation_duration": self.evaluation_duration,
                "throughput": self.throughput
            },
            "statistics": {
                "score_std": self.score_std,
                "cost_std": self.cost_std,
                "latency_std": self.latency_std
            }
        }


class MetricsCalculator:
    """Calculate advanced metrics from evaluation results."""
    
    def calculate_comprehensive_metrics(
        self,
        results: List[Dict[str, Any]],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> EvaluationMetrics:
        """Calculate comprehensive evaluation metrics.
        
        Args:
            results: List of evaluation results
            start_time: Evaluation start time
            end_time: Evaluation end time
            
        Returns:
            Comprehensive evaluation metrics
        """
        if not results:
            return self._empty_metrics()
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(results)
        
        # Basic metrics
        total_tests = len(results)
        passed_tests = df['success'].sum() if 'success' in df.columns else 0
        failed_tests = total_tests - passed_tests
        pass_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        scores = df['score'].fillna(0) if 'score' in df.columns else pd.Series([0] * total_tests)
        average_score = scores.mean()
        score_std = scores.std()
        
        # Performance metrics
        costs = df['cost'].fillna(0) if 'cost' in df.columns else pd.Series([0] * total_tests)
        latencies = df['latency'].fillna(0) if 'latency' in df.columns else pd.Series([0] * total_tests)
        
        total_cost = costs.sum()
        average_cost = costs.mean()
        cost_std = costs.std()
        
        total_latency = latencies.sum()
        average_latency = latencies.mean()
        latency_std = latencies.std()
        
        # Quality metrics
        score_distribution = self._calculate_score_distribution(scores)
        assertion_pass_rates = self._calculate_assertion_pass_rates(results)
        
        # Provider metrics
        provider_stats = self._calculate_provider_statistics(df)
        
        # Time-based metrics
        evaluation_duration = 0.0
        throughput = 0.0
        if start_time and end_time:
            evaluation_duration = (end_time - start_time).total_seconds()
            throughput = total_tests / evaluation_duration if evaluation_duration > 0 else 0
        
        return EvaluationMetrics(
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            pass_rate=pass_rate,
            average_score=average_score,
            total_cost=total_cost,
            average_cost=average_cost,
            total_latency=total_latency,
            average_latency=average_latency,
            score_distribution=score_distribution,
            assertion_pass_rates=assertion_pass_rates,
            provider_stats=provider_stats,
            evaluation_duration=evaluation_duration,
            throughput=throughput,
            score_std=score_std,
            cost_std=cost_std,
            latency_std=latency_std
        )
    
    def _empty_metrics(self) -> EvaluationMetrics:
        """Return empty metrics for zero results."""
        return EvaluationMetrics(
            total_tests=0,
            passed_tests=0,
            failed_tests=0,
            pass_rate=0.0,
            average_score=0.0,
            total_cost=0.0,
            average_cost=0.0,
            total_latency=0.0,
            average_latency=0.0,
            score_distribution={},
            assertion_pass_rates={},
            provider_stats={},
            evaluation_duration=0.0,
            throughput=0.0,
            score_std=0.0,
            cost_std=0.0,
            latency_std=0.0
        )
    
    def _calculate_score_distribution(self, scores: pd.Series) -> Dict[str, int]:
        """Calculate score distribution in ranges."""
        distribution = {
            "0.0-0.2": 0,
            "0.2-0.4": 0,
            "0.4-0.6": 0,
            "0.6-0.8": 0,
            "0.8-1.0": 0
        }
        
        for score in scores:
            if score <= 0.2:
                distribution["0.0-0.2"] += 1
            elif score <= 0.4:
                distribution["0.2-0.4"] += 1
            elif score <= 0.6:
                distribution["0.4-0.6"] += 1
            elif score <= 0.8:
                distribution["0.6-0.8"] += 1
            else:
                distribution["0.8-1.0"] += 1
        
        return distribution
    
    def _calculate_assertion_pass_rates(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate pass rates for each assertion type."""
        assertion_stats = defaultdict(lambda: {"total": 0, "passed": 0})
        
        for result in results:
            assertion_results = result.get('assertion_results', [])
            for assertion in assertion_results:
                assertion_type = assertion.get('type', 'unknown')
                assertion_stats[assertion_type]["total"] += 1
                if assertion.get('passed', False):
                    assertion_stats[assertion_type]["passed"] += 1
        
        pass_rates = {}
        for assertion_type, stats in assertion_stats.items():
            if stats["total"] > 0:
                pass_rates[assertion_type] = stats["passed"] / stats["total"]
            else:
                pass_rates[assertion_type] = 0.0
        
        return pass_rates
    
    def _calculate_provider_statistics(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Calculate per-provider statistics."""
        if 'provider' not in df.columns:
            return {}
        
        provider_stats = {}
        
        for provider in df['provider'].unique():
            provider_df = df[df['provider'] == provider]
            
            stats = {
                "total_tests": len(provider_df),
                "pass_rate": provider_df['success'].mean() if 'success' in provider_df.columns else 0,
                "average_score": provider_df['score'].mean() if 'score' in provider_df.columns else 0,
                "average_cost": provider_df['cost'].mean() if 'cost' in provider_df.columns else 0,
                "average_latency": provider_df['latency'].mean() if 'latency' in provider_df.columns else 0,
                "total_cost": provider_df['cost'].sum() if 'cost' in provider_df.columns else 0,
                "score_std": provider_df['score'].std() if 'score' in provider_df.columns else 0
            }
            
            provider_stats[provider] = stats
        
        return provider_stats
    
    def calculate_cost_efficiency(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate cost efficiency metrics.
        
        Args:
            results: List of evaluation results
            
        Returns:
            Cost efficiency metrics
        """
        if not results:
            return {}
        
        df = pd.DataFrame(results)
        
        # Cost per successful test
        successful_results = df[df['success'] == True] if 'success' in df.columns else df
        cost_per_success = (df['cost'].sum() / len(successful_results)) if len(successful_results) > 0 else 0
        
        # Cost per score point
        total_score = df['score'].sum() if 'score' in df.columns else 0
        cost_per_score = (df['cost'].sum() / total_score) if total_score > 0 else 0
        
        # Cost efficiency by provider
        provider_efficiency = {}
        if 'provider' in df.columns:
            for provider in df['provider'].unique():
                provider_df = df[df['provider'] == provider]
                provider_successful = provider_df[provider_df['success'] == True] if 'success' in provider_df.columns else provider_df
                
                if len(provider_successful) > 0:
                    provider_cost_per_success = provider_df['cost'].sum() / len(provider_successful)
                    provider_efficiency[provider] = provider_cost_per_success
        
        return {
            "cost_per_successful_test": cost_per_success,
            "cost_per_score_point": cost_per_score,
            "provider_cost_efficiency": provider_efficiency
        }
    
    def calculate_performance_trends(
        self,
        historical_results: List[Dict[str, Any]],
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """Calculate performance trends over time.
        
        Args:
            historical_results: Historical evaluation results with timestamps
            time_window_hours: Time window for trend analysis
            
        Returns:
            Performance trend metrics
        """
        if not historical_results:
            return {}
        
        # Convert to DataFrame
        df = pd.DataFrame(historical_results)
        
        # Ensure timestamp column
        if 'timestamp' not in df.columns:
            return {"error": "No timestamp data available for trend analysis"}
        
        # Convert timestamps
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Filter to time window
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        recent_df = df[df['timestamp'] >= cutoff_time]
        
        if len(recent_df) < 2:
            return {"error": "Insufficient data for trend analysis"}
        
        # Calculate hourly aggregations
        recent_df['hour'] = recent_df['timestamp'].dt.floor('H')
        hourly_stats = recent_df.groupby('hour').agg({
            'score': ['mean', 'std', 'count'],
            'cost': ['mean', 'sum'],
            'latency': ['mean'],
            'success': 'mean'
        }).reset_index()
        
        # Flatten column names
        hourly_stats.columns = ['_'.join(col).strip('_') for col in hourly_stats.columns]
        
        # Calculate trends
        if len(hourly_stats) >= 2:
            score_trend = np.polyfit(range(len(hourly_stats)), hourly_stats['score_mean'], 1)[0]
            cost_trend = np.polyfit(range(len(hourly_stats)), hourly_stats['cost_mean'], 1)[0]
            latency_trend = np.polyfit(range(len(hourly_stats)), hourly_stats['latency_mean'], 1)[0]
            success_trend = np.polyfit(range(len(hourly_stats)), hourly_stats['success_mean'], 1)[0]
        else:
            score_trend = cost_trend = latency_trend = success_trend = 0
        
        return {
            "time_window_hours": time_window_hours,
            "total_evaluations": len(recent_df),
            "hourly_data": hourly_stats.to_dict('records'),
            "trends": {
                "score_trend": score_trend,
                "cost_trend": cost_trend,
                "latency_trend": latency_trend,
                "success_rate_trend": success_trend
            },
            "trend_direction": {
                "score": "improving" if score_trend > 0 else "declining" if score_trend < 0 else "stable",
                "cost": "increasing" if cost_trend > 0 else "decreasing" if cost_trend < 0 else "stable",
                "latency": "increasing" if latency_trend > 0 else "decreasing" if latency_trend < 0 else "stable",
                "success_rate": "improving" if success_trend > 0 else "declining" if success_trend < 0 else "stable"
            }
        }
    
    def generate_insights(self, metrics: EvaluationMetrics) -> List[str]:
        """Generate actionable insights from metrics.
        
        Args:
            metrics: Calculated evaluation metrics
            
        Returns:
            List of insight strings
        """
        insights = []
        
        # Pass rate insights
        if metrics.pass_rate < 0.8:
            insights.append(f"Pass rate of {metrics.pass_rate*100:.1f}% is below recommended 80%. Consider reviewing test cases or model performance.")
        elif metrics.pass_rate > 0.95:
            insights.append(f"Excellent pass rate of {metrics.pass_rate*100:.1f}%. Tests may be too easy or model performance is exceptional.")
        
        # Score insights
        if metrics.average_score < 0.7:
            insights.append(f"Average score of {metrics.average_score:.3f} suggests room for improvement in model responses.")
        elif metrics.average_score > 0.9:
            insights.append(f"High average score of {metrics.average_score:.3f} indicates strong model performance.")
        
        # Cost insights
        if metrics.total_cost > 1.0:
            insights.append(f"Total cost of ${metrics.total_cost:.2f} is significant. Consider cost optimization strategies.")
        
        if metrics.average_cost > 0.01:
            insights.append(f"Average cost per test of ${metrics.average_cost:.4f} is high. Consider using more cost-effective providers.")
        
        # Latency insights
        if metrics.average_latency > 5.0:
            insights.append(f"Average latency of {metrics.average_latency:.1f}s is high. Consider optimizing for speed.")
        elif metrics.average_latency < 1.0:
            insights.append(f"Excellent average latency of {metrics.average_latency:.2f}s indicates good performance.")
        
        # Provider comparison insights
        if len(metrics.provider_stats) > 1:
            providers = list(metrics.provider_stats.keys())
            scores = [stats['average_score'] for stats in metrics.provider_stats.values()]
            costs = [stats['average_cost'] for stats in metrics.provider_stats.values()]
            
            best_score_provider = providers[np.argmax(scores)]
            best_cost_provider = providers[np.argmin(costs)]
            
            if best_score_provider != best_cost_provider:
                insights.append(f"{best_score_provider} has the highest quality scores, while {best_cost_provider} is most cost-effective.")
            else:
                insights.append(f"{best_score_provider} offers the best balance of quality and cost.")
        
        # Score distribution insights
        high_scores = metrics.score_distribution.get("0.8-1.0", 0)
        low_scores = metrics.score_distribution.get("0.0-0.2", 0)
        
        if high_scores > metrics.total_tests * 0.8:
            insights.append("Most results are high-quality (80%+ of tests scored 0.8+).")
        elif low_scores > metrics.total_tests * 0.2:
            insights.append(f"{low_scores} tests ({low_scores/metrics.total_tests*100:.1f}%) scored poorly (0.0-0.2). Review these cases.")
        
        # Throughput insights
        if metrics.throughput > 0:
            if metrics.throughput < 1.0:
                insights.append(f"Throughput of {metrics.throughput:.2f} tests/second is low. Consider parallel processing.")
            elif metrics.throughput > 10.0:
                insights.append(f"Excellent throughput of {metrics.throughput:.1f} tests/second.")
        
        return insights
    
    def compare_evaluations(
        self,
        baseline_results: List[Dict[str, Any]],
        comparison_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compare two sets of evaluation results.
        
        Args:
            baseline_results: Baseline evaluation results
            comparison_results: Results to compare against baseline
            
        Returns:
            Comparison metrics and insights
        """
        baseline_metrics = self.calculate_comprehensive_metrics(baseline_results)
        comparison_metrics = self.calculate_comprehensive_metrics(comparison_results)
        
        # Calculate deltas
        deltas = {
            "pass_rate": comparison_metrics.pass_rate - baseline_metrics.pass_rate,
            "average_score": comparison_metrics.average_score - baseline_metrics.average_score,
            "average_cost": comparison_metrics.average_cost - baseline_metrics.average_cost,
            "average_latency": comparison_metrics.average_latency - baseline_metrics.average_latency,
            "total_cost": comparison_metrics.total_cost - baseline_metrics.total_cost
        }
        
        # Generate comparison insights
        insights = []
        
        if deltas["pass_rate"] > 0.05:
            insights.append(f"Pass rate improved by {deltas['pass_rate']*100:.1f}%")
        elif deltas["pass_rate"] < -0.05:
            insights.append(f"Pass rate declined by {abs(deltas['pass_rate'])*100:.1f}%")
        
        if deltas["average_score"] > 0.05:
            insights.append(f"Average score improved by {deltas['average_score']:.3f}")
        elif deltas["average_score"] < -0.05:
            insights.append(f"Average score declined by {abs(deltas['average_score']):.3f}")
        
        if deltas["average_cost"] < -0.001:
            insights.append(f"Cost efficiency improved by ${abs(deltas['average_cost']):.4f} per test")
        elif deltas["average_cost"] > 0.001:
            insights.append(f"Cost increased by ${deltas['average_cost']:.4f} per test")
        
        return {
            "baseline_metrics": baseline_metrics.to_dict(),
            "comparison_metrics": comparison_metrics.to_dict(),
            "deltas": deltas,
            "insights": insights,
            "recommendation": self._generate_recommendation(deltas)
        }
    
    def _generate_recommendation(self, deltas: Dict[str, float]) -> str:
        """Generate recommendation based on comparison deltas."""
        if deltas["average_score"] > 0.05 and deltas["average_cost"] <= 0:
            return "Strong improvement: Better quality at same or lower cost. Recommended for production."
        elif deltas["average_score"] > 0.05:
            return "Quality improved but at higher cost. Evaluate if the improvement justifies the expense."
        elif deltas["average_cost"] < -0.001 and deltas["average_score"] >= -0.02:
            return "Cost efficiency improved with minimal quality impact. Good optimization."
        elif deltas["pass_rate"] < -0.1:
            return "Significant decline in pass rate. Investigate before deploying."
        else:
            return "Mixed results. Further evaluation recommended."