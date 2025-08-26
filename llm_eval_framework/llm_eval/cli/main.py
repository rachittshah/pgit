"""
Main CLI interface for LLM Evaluation Framework.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..config.loader import ConfigLoader, ConfigLoaderError
from ..evaluation.evaluator import Evaluator, EvaluationError
from ..reporting.html_generator import HTMLReportGenerator
from ..reporting.pdf_generator import PDFReportGenerator
from ..analytics.metrics import MetricsCalculator


console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """LLM Evaluation Framework: Universal LLM testing with multi-provider support via LiteLLM."""
    pass


@cli.command()
@click.option(
    "--config", "-c", 
    type=click.Path(exists=True), 
    help="Path to configuration file"
)
@click.option(
    "--output", "-o", 
    type=click.Path(), 
    help="Output file for results"
)
@click.option(
    "--format", "output_format", 
    type=click.Choice(["json", "table", "html", "pdf"]), 
    default="table",
    help="Output format"
)
@click.option(
    "--verbose", "-v", 
    is_flag=True, 
    help="Verbose output"
)
def eval(config: Optional[str], output: Optional[str], output_format: str, verbose: bool):
    """Run evaluations based on configuration."""
    
    try:
        # Load configuration
        loader = ConfigLoader()
        
        if config:
            config_obj = loader.load_config(Path(config))
        else:
            config_obj = loader.load_default_config()
        
        console.print(f"[green]✓[/green] Loaded configuration: {config_obj.description or 'Unnamed evaluation'}")
        
        # Validate configuration and show warnings
        warnings = loader.validate_config(config_obj)
        for warning in warnings:
            console.print(f"[yellow]⚠[/yellow] {warning}")
        
        # Run evaluation
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Running evaluations...", total=None)
            
            evaluator = Evaluator(config_obj)
            
            # Validate providers first
            progress.update(task, description="Validating providers...")
            validation_results = asyncio.run(evaluator.validate_providers())
            
            failed_providers = [
                provider_id for provider_id, valid in validation_results.items() 
                if not valid
            ]
            
            if failed_providers:
                console.print(f"[red]✗[/red] Failed to validate providers: {', '.join(failed_providers)}")
                sys.exit(1)
            
            console.print(f"[green]✓[/green] Validated {len(validation_results)} providers")
            
            # Run evaluations
            progress.update(task, description="Running tests...")
            summary = asyncio.run(evaluator.evaluate())
            
            progress.update(task, description="Complete!")
        
        # Display results
        _display_results(summary, output_format, verbose)
        
        # Save results if output specified
        if output:
            _save_results(summary, Path(output), output_format, config_obj)
            console.print(f"[green]✓[/green] Results saved to {output}")
        
        # Exit with appropriate code
        if summary.failed_tests > 0:
            console.print(f"\n[red]Evaluation completed with {summary.failed_tests} failures[/red]")
            sys.exit(1)
        else:
            console.print(f"\n[green]All {summary.total_tests} tests passed![/green]")
            
    except ConfigLoaderError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        sys.exit(1)
    except EvaluationError as e:
        console.print(f"[red]Evaluation error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option(
    "--directory", "-d", 
    type=click.Path(exists=True), 
    default=".",
    help="Directory to initialize configuration in"
)
def init(directory: str):
    """Initialize a new LLM evaluation project."""
    
    try:
        project_dir = Path(directory)
        config_path = project_dir / "llmeval.yaml"
        
        if config_path.exists():
            if not click.confirm(f"Configuration file already exists at {config_path}. Overwrite?"):
                console.print("Initialization cancelled.")
                return
        
        # Create example configuration
        loader = ConfigLoader()
        example_config = loader.create_example_config()
        
        # Write configuration to YAML
        import yaml
        with open(config_path, "w") as f:
            # Convert to dict first
            config_dict = example_config.dict(by_alias=True, exclude_none=True)
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
        
        console.print(f"[green]✓[/green] Created configuration file: {config_path}")
        console.print("\nNext steps:")
        console.print("1. Edit llmeval.yaml to configure your prompts and providers")
        console.print("2. Set required environment variables (e.g., OPENAI_API_KEY)")
        console.print("3. Run: llm-eval eval")
        
    except Exception as e:
        console.print(f"[red]Error initializing project:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--config", "-c", 
    type=click.Path(exists=True), 
    help="Path to configuration file"
)
def validate(config: Optional[str]):
    """Validate configuration file."""
    
    try:
        loader = ConfigLoader()
        
        if config:
            config_obj = loader.load_config(Path(config))
            config_path = config
        else:
            config_obj = loader.load_default_config()
            config_path = "default configuration"
        
        console.print(f"[green]✓[/green] Configuration file is valid: {config_path}")
        
        # Show warnings
        warnings = loader.validate_config(config_obj)
        if warnings:
            console.print("\n[yellow]Warnings:[/yellow]")
            for warning in warnings:
                console.print(f"  • {warning}")
        
        # Show configuration summary
        console.print(f"\n[blue]Summary:[/blue]")
        console.print(f"  • Prompts: {len(config_obj.prompts)}")
        console.print(f"  • Providers: {len(config_obj.providers)}")
        console.print(f"  • Tests: {len(config_obj.tests or [])}")
        if config_obj.redteam:
            console.print(f"  • Red team plugins: {len(config_obj.redteam.plugins or [])}")
        
    except ConfigLoaderError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error validating configuration:[/red] {e}")
        sys.exit(1)


@cli.command("list-providers")
def list_providers():
    """List available providers."""
    
    from ..providers.registry import get_available_providers
    
    providers = get_available_providers()
    
    if not providers:
        console.print("No providers available.")
        return
    
    table = Table(title="Available Providers")
    table.add_column("Provider", style="cyan")
    table.add_column("Class", style="green")
    table.add_column("Models", style="yellow")
    
    for provider_name, provider_class in providers.items():
        models = []
        if hasattr(provider_class, "get_available_models"):
            models = provider_class.get_available_models()
        
        models_str = ", ".join(models[:3])
        if len(models) > 3:
            models_str += f" ... ({len(models)} total)"
        
        table.add_row(
            provider_name,
            provider_class.__name__,
            models_str or "Unknown"
        )
    
    console.print(table)


@cli.command()
@click.option(
    "--results", "-r",
    type=click.Path(exists=True),
    required=True,
    help="Path to evaluation results JSON file"
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="Output file path"
)
@click.option(
    "--format", "output_format",
    type=click.Choice(["html", "pdf"]),
    default="html",
    help="Report format"
)
def report(results: str, output: Optional[str], output_format: str):
    """Generate detailed report from evaluation results."""
    
    try:
        # Load results
        with open(results, 'r') as f:
            results_data = json.load(f)
        
        # Extract results and config
        if 'results' in results_data:
            eval_results = results_data['results']
            config_data = results_data.get('config', {})
        else:
            # Assume it's a list of results
            eval_results = results_data if isinstance(results_data, list) else [results_data]
            config_data = {}
        
        # Determine output path
        if not output:
            base_path = Path(results).parent / Path(results).stem
            output = base_path.with_suffix(f'.{output_format}')
        else:
            output = Path(output)
        
        # Generate report
        if output_format == "html":
            generator = HTMLReportGenerator()
            generator.generate_report(eval_results, config_data, output)
        elif output_format == "pdf":
            try:
                generator = PDFReportGenerator()
                generator.generate_report(eval_results, config_data, output)
            except ImportError as e:
                console.print(f"[red]Error:[/red] PDF generation requires additional dependencies: {e}")
                console.print("Install with: pip install weasyprint or pip install reportlab")
                sys.exit(1)
        
        console.print(f"[green]✓[/green] Report generated: {output}")
        
    except Exception as e:
        console.print(f"[red]Error generating report:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--results", "-r",
    type=click.Path(exists=True),
    required=True,
    help="Path to evaluation results JSON file"
)
def analyze(results: str):
    """Analyze evaluation results and show insights."""
    
    try:
        # Load results
        with open(results, 'r') as f:
            results_data = json.load(f)
        
        # Extract results
        if 'results' in results_data:
            eval_results = results_data['results']
        else:
            eval_results = results_data if isinstance(results_data, list) else [results_data]
        
        # Calculate metrics
        calculator = MetricsCalculator()
        metrics = calculator.calculate_comprehensive_metrics(eval_results)
        
        # Display metrics
        console.print("\n[bold]📊 Evaluation Analytics[/bold]")
        
        # Basic metrics
        table = Table(title="Performance Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Tests", str(metrics.total_tests))
        table.add_row("Pass Rate", f"{metrics.pass_rate:.1%}")
        table.add_row("Average Score", f"{metrics.average_score:.3f}")
        table.add_row("Total Cost", f"${metrics.total_cost:.4f}")
        table.add_row("Average Latency", f"{metrics.average_latency:.2f}s")
        table.add_row("Throughput", f"{metrics.throughput:.1f} tests/sec")
        
        console.print(table)
        
        # Score distribution
        if metrics.score_distribution:
            console.print("\n[bold]Score Distribution[/bold]")
            for range_label, count in metrics.score_distribution.items():
                percentage = (count / metrics.total_tests * 100) if metrics.total_tests > 0 else 0
                bar = "█" * int(percentage / 5)  # Scale bar
                console.print(f"{range_label}: {count:3d} ({percentage:5.1f}%) {bar}")
        
        # Provider comparison
        if len(metrics.provider_stats) > 1:
            console.print("\n[bold]Provider Comparison[/bold]")
            provider_table = Table()
            provider_table.add_column("Provider", style="cyan")
            provider_table.add_column("Pass Rate", style="green")
            provider_table.add_column("Avg Score", style="yellow")
            provider_table.add_column("Avg Cost", style="red")
            provider_table.add_column("Avg Latency", style="magenta")
            
            for provider, stats in metrics.provider_stats.items():
                provider_table.add_row(
                    provider,
                    f"{stats['pass_rate']:.1%}",
                    f"{stats['average_score']:.3f}",
                    f"${stats['average_cost']:.4f}",
                    f"{stats['average_latency']:.2f}s"
                )
            
            console.print(provider_table)
        
        # Insights
        insights = calculator.generate_insights(metrics)
        if insights:
            console.print("\n[bold]💡 Insights[/bold]")
            for insight in insights:
                console.print(f"  • {insight}")
        
    except Exception as e:
        console.print(f"[red]Error analyzing results:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--baseline", "-b",
    type=click.Path(exists=True),
    required=True,
    help="Path to baseline results JSON file"
)
@click.option(
    "--comparison", "-c",
    type=click.Path(exists=True),
    required=True,
    help="Path to comparison results JSON file"
)
def compare(baseline: str, comparison: str):
    """Compare two sets of evaluation results."""
    
    try:
        # Load results
        with open(baseline, 'r') as f:
            baseline_data = json.load(f)
        
        with open(comparison, 'r') as f:
            comparison_data = json.load(f)
        
        # Extract results
        def extract_results(data):
            if 'results' in data:
                return data['results']
            return data if isinstance(data, list) else [data]
        
        baseline_results = extract_results(baseline_data)
        comparison_results = extract_results(comparison_data)
        
        # Compare
        calculator = MetricsCalculator()
        comparison_report = calculator.compare_evaluations(baseline_results, comparison_results)
        
        # Display comparison
        console.print("\n[bold]📊 Evaluation Comparison[/bold]")
        
        # Deltas table
        deltas = comparison_report['deltas']
        table = Table(title="Performance Changes")
        table.add_column("Metric", style="cyan")
        table.add_column("Baseline", style="blue")
        table.add_column("Comparison", style="green")
        table.add_column("Change", style="yellow")
        
        baseline_metrics = comparison_report['baseline_metrics']['basic_metrics']
        comparison_metrics = comparison_report['comparison_metrics']['basic_metrics']
        
        # Format changes with colors
        def format_change(delta, format_str=".3f", is_percentage=False):
            if is_percentage:
                delta_str = f"{delta*100:+.1f}%"
                color = "green" if delta > 0 else "red" if delta < 0 else "white"
            else:
                delta_str = f"{delta:+{format_str}}"
                color = "green" if delta > 0 else "red" if delta < 0 else "white"
            return f"[{color}]{delta_str}[/{color}]"
        
        table.add_row(
            "Pass Rate",
            f"{baseline_metrics['pass_rate']:.1%}",
            f"{comparison_metrics['pass_rate']:.1%}",
            format_change(deltas['pass_rate'], is_percentage=True)
        )
        
        table.add_row(
            "Average Score",
            f"{baseline_metrics['average_score']:.3f}",
            f"{comparison_metrics['average_score']:.3f}",
            format_change(deltas['average_score'])
        )
        
        baseline_perf = comparison_report['baseline_metrics']['performance_metrics']
        comparison_perf = comparison_report['comparison_metrics']['performance_metrics']
        
        table.add_row(
            "Average Cost",
            f"${baseline_perf['average_cost']:.4f}",
            f"${comparison_perf['average_cost']:.4f}",
            format_change(deltas['average_cost'], ".4f")
        )
        
        table.add_row(
            "Average Latency",
            f"{baseline_perf['average_latency']:.2f}s",
            f"{comparison_perf['average_latency']:.2f}s",
            format_change(deltas['average_latency'], ".2f")
        )
        
        console.print(table)
        
        # Insights
        insights = comparison_report['insights']
        if insights:
            console.print("\n[bold]💡 Insights[/bold]")
            for insight in insights:
                console.print(f"  • {insight}")
        
        # Recommendation
        recommendation = comparison_report['recommendation']
        console.print(f"\n[bold]📝 Recommendation[/bold]")
        console.print(f"  {recommendation}")
        
    except Exception as e:
        console.print(f"[red]Error comparing results:[/red] {e}")
        sys.exit(1)


def _display_results(summary, output_format: str, verbose: bool):
    """Display evaluation results."""
    
    if output_format == "json":
        console.print(json.dumps(summary.dict(), indent=2))
        return
    
    # Table format
    console.print(f"\n[bold]Evaluation Summary[/bold]")
    console.print(f"Total tests: {summary.total_tests}")
    console.print(f"Passed: [green]{summary.passed_tests}[/green]")
    console.print(f"Failed: [red]{summary.failed_tests}[/red]")
    console.print(f"Pass rate: {summary.pass_rate:.1%}")
    
    if summary.total_cost is not None:
        console.print(f"Total cost: ${summary.total_cost:.4f}")
    
    if summary.average_latency is not None:
        console.print(f"Average latency: {summary.average_latency:.2f}s")
    
    # Detailed results table
    if verbose or summary.failed_tests > 0:
        table = Table(title="Test Results")
        table.add_column("Provider", style="cyan")
        table.add_column("Test", style="blue")
        table.add_column("Status", style="green")
        table.add_column("Response", style="white")
        table.add_column("Cost", style="yellow")
        table.add_column("Latency", style="magenta")
        
        for result in summary.results:
            status = "[green]✓[/green]" if result.success else "[red]✗[/red]"
            response = result.response[:50] + "..." if len(result.response) > 50 else result.response
            cost = f"${result.cost:.4f}" if result.cost else "-"
            latency = f"{result.latency:.2f}s" if result.latency else "-"
            test_desc = str(result.vars) if result.vars else "No vars"
            
            table.add_row(
                result.provider_id,
                test_desc,
                status,
                response,
                cost,
                latency
            )
        
        console.print(table)
    
    # Show failures
    if summary.failed_tests > 0 and not verbose:
        console.print(f"\n[red]Failures ({summary.failed_tests}):[/red]")
        for result in summary.results:
            if not result.success:
                console.print(f"  • {result.provider_id}: {result.error or 'Assertion failed'}")


def _save_results(summary, output_path: Path, output_format: str, config_obj):
    """Save evaluation results to file."""
    
    # Convert results to standard format
    results = [result.dict() for result in summary.results]
    config_dict = config_obj.dict() if hasattr(config_obj, 'dict') else {}
    
    if output_format == "json":
        with open(output_path, "w") as f:
            json.dump(summary.dict(), f, indent=2)
    
    elif output_format == "html":
        html_generator = HTMLReportGenerator()
        html_generator.generate_report(results, config_dict, output_path)
    
    elif output_format == "pdf":
        try:
            pdf_generator = PDFReportGenerator()
            pdf_generator.generate_report(results, config_dict, output_path)
        except ImportError as e:
            console.print(f"[yellow]Warning:[/yellow] PDF generation requires additional dependencies: {e}")
            console.print("Falling back to JSON format.")
            with open(output_path.with_suffix('.json'), "w") as f:
                json.dump(summary.dict(), f, indent=2)
    
    else:
        # Default to JSON for unknown formats
        with open(output_path, "w") as f:
            json.dump(summary.dict(), f, indent=2)


if __name__ == "__main__":
    cli()