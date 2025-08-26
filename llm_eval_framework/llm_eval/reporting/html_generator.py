"""
HTML report generation for LLM evaluation results.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, Template


class HTMLReportGenerator:
    """Generate HTML reports from evaluation results."""
    
    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize HTML report generator.
        
        Args:
            template_dir: Directory containing HTML templates
        """
        self.template_dir = template_dir or Path(__file__).parent / "templates"
        self.template_dir.mkdir(exist_ok=True)
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )
        
        # Create default templates if they don't exist
        self._ensure_templates_exist()
    
    def _ensure_templates_exist(self):
        """Create default HTML templates if they don't exist."""
        
        # Main report template
        main_template_path = self.template_dir / "report.html"
        if not main_template_path.exists():
            self._create_main_template(main_template_path)
        
        # Summary template
        summary_template_path = self.template_dir / "summary.html"
        if not summary_template_path.exists():
            self._create_summary_template(summary_template_path)
    
    def _create_main_template(self, path: Path):
        """Create main report HTML template."""
        template_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM Evaluation Report - {{ config.description or "Evaluation Results" }}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            line-height: 1.6; 
            color: #333; 
            background: #f5f7fa;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 40px 20px; 
            text-align: center; 
            border-radius: 10px; 
            margin-bottom: 30px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; font-weight: 300; }
        .header p { font-size: 1.2em; opacity: 0.9; }
        .summary-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 20px; 
            margin-bottom: 30px; 
        }
        .summary-card { 
            background: white; 
            padding: 25px; 
            border-radius: 10px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
            text-align: center; 
            transition: transform 0.2s;
        }
        .summary-card:hover { transform: translateY(-2px); }
        .summary-card h3 { color: #667eea; margin-bottom: 10px; font-size: 0.9em; text-transform: uppercase; letter-spacing: 1px; }
        .summary-card .value { font-size: 2.2em; font-weight: bold; color: #333; margin-bottom: 5px; }
        .summary-card .subtitle { color: #666; font-size: 0.9em; }
        .chart-container { 
            background: white; 
            padding: 30px; 
            border-radius: 10px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
            margin-bottom: 30px; 
        }
        .chart-title { font-size: 1.3em; margin-bottom: 20px; color: #333; text-align: center; }
        .results-section { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .result-item { 
            border-left: 4px solid #667eea; 
            padding: 20px; 
            margin-bottom: 20px; 
            background: #f8f9ff; 
            border-radius: 0 8px 8px 0; 
        }
        .result-header { display: flex; justify-content: between; align-items: center; margin-bottom: 15px; }
        .result-provider { color: #667eea; font-weight: bold; font-size: 1.1em; }
        .result-score { 
            background: linear-gradient(45deg, #667eea, #764ba2); 
            color: white; 
            padding: 8px 16px; 
            border-radius: 20px; 
            font-weight: bold; 
        }
        .result-details { margin-top: 15px; }
        .assertion-results { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin-top: 10px; }
        .assertion { padding: 10px; border-radius: 5px; font-size: 0.9em; }
        .assertion.passed { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .assertion.failed { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .metadata { margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee; font-size: 0.9em; color: #666; }
        .metadata-item { margin: 5px 0; }
        .provider-comparison { margin: 30px 0; }
        .cost-chart, .latency-chart { width: 100%; height: 300px; }
        .footer { 
            text-align: center; 
            margin-top: 40px; 
            padding: 20px; 
            color: #666; 
            border-top: 1px solid #eee; 
        }
        
        @media (max-width: 768px) {
            .container { padding: 10px; }
            .header { padding: 20px 10px; }
            .header h1 { font-size: 2em; }
            .summary-grid { grid-template-columns: 1fr; }
            .result-header { flex-direction: column; align-items: flex-start; }
            .result-score { margin-top: 10px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ config.description or "LLM Evaluation Report" }}</h1>
            <p>Generated on {{ timestamp.strftime('%B %d, %Y at %I:%M %p') }}</p>
            {% if config.providers %}
                <p>Providers: {{ config.providers | join(', ') }}</p>
            {% endif %}
        </div>
        
        <div class="summary-grid">
            <div class="summary-card">
                <h3>Total Tests</h3>
                <div class="value">{{ summary.total_tests }}</div>
                <div class="subtitle">Test cases executed</div>
            </div>
            <div class="summary-card">
                <h3>Success Rate</h3>
                <div class="value">{{ "%.1f"|format(summary.pass_rate * 100) }}%</div>
                <div class="subtitle">{{ summary.passed_tests }}/{{ summary.total_tests }} passed</div>
            </div>
            <div class="summary-card">
                <h3>Average Score</h3>
                <div class="value">{{ "%.3f"|format(summary.average_score) }}</div>
                <div class="subtitle">Weighted average</div>
            </div>
            <div class="summary-card">
                <h3>Total Cost</h3>
                <div class="value">${{ "%.4f"|format(summary.total_cost) }}</div>
                <div class="subtitle">API usage cost</div>
            </div>
            <div class="summary-card">
                <h3>Avg Latency</h3>
                <div class="value">{{ "%.0f"|format(summary.average_latency * 1000) }}ms</div>
                <div class="subtitle">Response time</div>
            </div>
        </div>
        
        {% if provider_stats and provider_stats|length > 1 %}
        <div class="provider-comparison">
            <div class="chart-container">
                <h3 class="chart-title">Provider Performance Comparison</h3>
                <canvas id="providerChart" width="400" height="200"></canvas>
            </div>
            
            <div class="chart-container">
                <h3 class="chart-title">Cost vs Latency Analysis</h3>
                <canvas id="costLatencyChart" class="cost-chart" width="400" height="200"></canvas>
            </div>
        </div>
        {% endif %}
        
        <div class="results-section">
            <h2 style="margin-bottom: 25px; color: #333;">Detailed Results</h2>
            
            {% for result in results %}
                <div class="result-item">
                    <div class="result-header">
                        <div>
                            <span class="result-provider">{{ result.provider }}</span>
                            {% if result.test_case and result.test_case.description %}
                                <div style="margin-top: 5px; color: #666;">{{ result.test_case.description }}</div>
                            {% endif %}
                        </div>
                        <div class="result-score">Score: {{ "%.3f"|format(result.score) }}</div>
                    </div>
                    
                    <div class="result-details">
                        <strong>Response:</strong>
                        <div style="margin: 10px 0; padding: 15px; background: white; border-radius: 5px; border: 1px solid #ddd; white-space: pre-wrap;">{{ result.response[:500] }}{% if result.response|length > 500 %}...{% endif %}</div>
                        
                        {% if result.assertion_results %}
                        <div class="assertion-results">
                            {% for assertion in result.assertion_results %}
                                <div class="assertion {{ 'passed' if assertion.passed else 'failed' }}">
                                    <strong>{{ assertion.type }}</strong><br>
                                    {{ assertion.message or ("✓ Passed" if assertion.passed else "✗ Failed") }}
                                    {% if assertion.score is not none %}
                                        <br>Score: {{ "%.3f"|format(assertion.score) }}
                                    {% endif %}
                                </div>
                            {% endfor %}
                        </div>
                        {% endif %}
                        
                        <div class="metadata">
                            <div class="metadata-item"><strong>Cost:</strong> ${{ "%.6f"|format(result.cost or 0) }}</div>
                            <div class="metadata-item"><strong>Latency:</strong> {{ "%.0f"|format((result.latency or 0) * 1000) }}ms</div>
                            {% if result.token_usage %}
                                <div class="metadata-item"><strong>Tokens:</strong> {{ result.token_usage.total_tokens }} ({{ result.token_usage.prompt_tokens }} prompt + {{ result.token_usage.completion_tokens }} completion)</div>
                            {% endif %}
                            {% if result.test_case and result.test_case.vars %}
                                <div class="metadata-item"><strong>Variables:</strong> {{ result.test_case.vars | tojson }}</div>
                            {% endif %}
                        </div>
                    </div>
                </div>
            {% endfor %}
        </div>
        
        <div class="footer">
            <p>Report generated by LLM Evaluation Framework</p>
            <p>{{ timestamp.strftime('%Y-%m-%d %H:%M:%S') }}</p>
        </div>
    </div>
    
    {% if provider_stats and provider_stats|length > 1 %}
    <script>
        // Provider Performance Chart
        const providerCtx = document.getElementById('providerChart').getContext('2d');
        new Chart(providerCtx, {
            type: 'bar',
            data: {
                labels: {{ provider_stats.keys() | list | tojson }},
                datasets: [{
                    label: 'Average Score',
                    data: {{ provider_stats.values() | map(attribute='average_score') | list | tojson }},
                    backgroundColor: 'rgba(102, 126, 234, 0.6)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 1
                }, {
                    label: 'Pass Rate (%)',
                    data: {{ provider_stats.values() | map(attribute='pass_rate') | map('multiply', 100) | list | tojson }},
                    backgroundColor: 'rgba(118, 75, 162, 0.6)',
                    borderColor: 'rgba(118, 75, 162, 1)',
                    borderWidth: 1,
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1.0,
                        position: 'left'
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        max: 100,
                        grid: {
                            drawOnChartArea: false,
                        },
                    }
                }
            }
        });
        
        // Cost vs Latency Scatter Chart
        const costLatencyCtx = document.getElementById('costLatencyChart').getContext('2d');
        const scatterData = [
            {% for provider, stats in provider_stats.items() %}
            {
                x: {{ stats.average_latency * 1000 }},
                y: {{ stats.average_cost }},
                label: '{{ provider }}'
            }{% if not loop.last %},{% endif %}
            {% endfor %}
        ];
        
        new Chart(costLatencyCtx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Cost vs Latency',
                    data: scatterData,
                    backgroundColor: 'rgba(102, 126, 234, 0.6)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    pointRadius: 8,
                    pointHoverRadius: 10
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.raw.label + ': $' + context.raw.y.toFixed(6) + ', ' + context.raw.x.toFixed(0) + 'ms';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Average Latency (ms)'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Average Cost ($)'
                        }
                    }
                }
            }
        });
    </script>
    {% endif %}
</body>
</html>"""
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(template_content)
    
    def _create_summary_template(self, path: Path):
        """Create summary HTML template."""
        template_content = """<div class="summary-report">
    <h2>Evaluation Summary</h2>
    <div class="summary-stats">
        <div class="stat-item">
            <span class="stat-label">Total Tests:</span>
            <span class="stat-value">{{ total_tests }}</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">Passed:</span>
            <span class="stat-value">{{ passed_tests }}</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">Success Rate:</span>
            <span class="stat-value">{{ "%.1f"|format(pass_rate * 100) }}%</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">Average Score:</span>
            <span class="stat-value">{{ "%.3f"|format(average_score) }}</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">Total Cost:</span>
            <span class="stat-value">${{ "%.4f"|format(total_cost) }}</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">Average Latency:</span>
            <span class="stat-value">{{ "%.0f"|format(average_latency * 1000) }}ms</span>
        </div>
    </div>
</div>"""
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(template_content)
    
    def generate_report(
        self,
        results: List[Dict[str, Any]],
        config: Dict[str, Any],
        output_path: Path,
        template_name: str = "report.html"
    ) -> Path:
        """Generate HTML report from evaluation results.
        
        Args:
            results: List of evaluation results
            config: Evaluation configuration
            output_path: Output file path
            template_name: Template file name
            
        Returns:
            Path to generated report
        """
        # Calculate summary statistics
        summary = self._calculate_summary(results)
        provider_stats = self._calculate_provider_stats(results)
        
        # Load template
        try:
            template = self.env.get_template(template_name)
        except Exception:
            # Fall back to basic template if custom template fails
            template = self.env.get_template("report.html")
        
        # Render report
        html_content = template.render(
            results=results,
            config=config,
            summary=summary,
            provider_stats=provider_stats,
            timestamp=datetime.now()
        )
        
        # Write report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
    def _calculate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics from results.
        
        Args:
            results: List of evaluation results
            
        Returns:
            Summary statistics
        """
        if not results:
            return {
                "total_tests": 0,
                "passed_tests": 0,
                "pass_rate": 0.0,
                "average_score": 0.0,
                "total_cost": 0.0,
                "average_latency": 0.0
            }
        
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.get('success', False))
        total_score = sum(r.get('score', 0) for r in results)
        total_cost = sum(r.get('cost', 0) for r in results)
        total_latency = sum(r.get('latency', 0) for r in results)
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "pass_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "average_score": total_score / total_tests if total_tests > 0 else 0,
            "total_cost": total_cost,
            "average_latency": total_latency / total_tests if total_tests > 0 else 0
        }
    
    def _calculate_provider_stats(self, results: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Calculate per-provider statistics.
        
        Args:
            results: List of evaluation results
            
        Returns:
            Per-provider statistics
        """
        provider_results = {}
        
        for result in results:
            provider = result.get('provider', 'unknown')
            if provider not in provider_results:
                provider_results[provider] = []
            provider_results[provider].append(result)
        
        provider_stats = {}
        for provider, provider_res in provider_results.items():
            summary = self._calculate_summary(provider_res)
            provider_stats[provider] = summary
        
        return provider_stats
    
    def generate_comparison_report(
        self,
        results_list: List[Dict[str, Any]],
        labels: List[str],
        output_path: Path
    ) -> Path:
        """Generate comparison report for multiple evaluation runs.
        
        Args:
            results_list: List of result sets to compare
            labels: Labels for each result set
            output_path: Output file path
            
        Returns:
            Path to generated report
        """
        # Calculate summaries for each result set
        summaries = [self._calculate_summary(results) for results in results_list]
        
        # Create comparison template
        template_content = """<!DOCTYPE html>
<html>
<head>
    <title>LLM Evaluation Comparison Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .comparison-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .comparison-table th, .comparison-table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        .comparison-table th { background-color: #f2f2f2; }
        .chart-container { width: 100%; height: 400px; margin: 30px 0; }
    </style>
</head>
<body>
    <h1>LLM Evaluation Comparison Report</h1>
    <p>Generated on {{ timestamp.strftime('%Y-%m-%d %H:%M:%S') }}</p>
    
    <h2>Summary Comparison</h2>
    <table class="comparison-table">
        <thead>
            <tr>
                <th>Metric</th>
                {% for label in labels %}
                <th>{{ label }}</th>
                {% endfor %}
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>Total Tests</strong></td>
                {% for summary in summaries %}
                <td>{{ summary.total_tests }}</td>
                {% endfor %}
            </tr>
            <tr>
                <td><strong>Success Rate</strong></td>
                {% for summary in summaries %}
                <td>{{ "%.1f"|format(summary.pass_rate * 100) }}%</td>
                {% endfor %}
            </tr>
            <tr>
                <td><strong>Average Score</strong></td>
                {% for summary in summaries %}
                <td>{{ "%.3f"|format(summary.average_score) }}</td>
                {% endfor %}
            </tr>
            <tr>
                <td><strong>Total Cost</strong></td>
                {% for summary in summaries %}
                <td>${{ "%.4f"|format(summary.total_cost) }}</td>
                {% endfor %}
            </tr>
            <tr>
                <td><strong>Average Latency</strong></td>
                {% for summary in summaries %}
                <td>{{ "%.0f"|format(summary.average_latency * 1000) }}ms</td>
                {% endfor %}
            </tr>
        </tbody>
    </table>
    
    <div class="chart-container">
        <canvas id="comparisonChart"></canvas>
    </div>
    
    <script>
        const ctx = document.getElementById('comparisonChart').getContext('2d');
        new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Success Rate', 'Avg Score', 'Cost Efficiency', 'Speed'],
                datasets: [
                    {% for i in range(summaries|length) %}
                    {
                        label: '{{ labels[i] }}',
                        data: [
                            {{ summaries[i].pass_rate * 100 }},
                            {{ summaries[i].average_score * 100 }},
                            {{ 100 - (summaries[i].total_cost * 10000) }}, // Inverse for efficiency
                            {{ 100 - (summaries[i].average_latency * 100) }} // Inverse for speed
                        ],
                        borderColor: 'hsl({{ i * 360 / summaries|length }}, 70%, 50%)',
                        backgroundColor: 'hsla({{ i * 360 / summaries|length }}, 70%, 50%, 0.2)',
                        pointBackgroundColor: 'hsl({{ i * 360 / summaries|length }}, 70%, 50%)',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: 'hsl({{ i * 360 / summaries|length }}, 70%, 50%)'
                    }{% if not loop.last %},{% endif %}
                    {% endfor %}
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    </script>
</body>
</html>"""
        
        # Render comparison report
        template = Template(template_content)
        html_content = template.render(
            summaries=summaries,
            labels=labels,
            timestamp=datetime.now()
        )
        
        # Write report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path