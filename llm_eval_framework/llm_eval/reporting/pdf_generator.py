"""
PDF report generation for LLM evaluation results.
"""

import base64
import io
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.charts.piecharts import Pie
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class PDFReportGenerator:
    """Generate PDF reports from evaluation results."""
    
    def __init__(self, use_weasyprint: bool = True):
        """Initialize PDF report generator.
        
        Args:
            use_weasyprint: Use WeasyPrint for HTML-to-PDF conversion (preferred)
        """
        self.use_weasyprint = use_weasyprint and WEASYPRINT_AVAILABLE
        
        if not self.use_weasyprint and not REPORTLAB_AVAILABLE:
            raise ImportError(
                "Neither WeasyPrint nor ReportLab is available. "
                "Install one of them: pip install weasyprint or pip install reportlab"
            )
    
    def generate_report(
        self,
        results: List[Dict[str, Any]],
        config: Dict[str, Any],
        output_path: Path
    ) -> Path:
        """Generate PDF report from evaluation results.
        
        Args:
            results: List of evaluation results
            config: Evaluation configuration
            output_path: Output file path
            
        Returns:
            Path to generated PDF report
        """
        if self.use_weasyprint:
            return self._generate_with_weasyprint(results, config, output_path)
        else:
            return self._generate_with_reportlab(results, config, output_path)
    
    def _generate_with_weasyprint(
        self,
        results: List[Dict[str, Any]],
        config: Dict[str, Any],
        output_path: Path
    ) -> Path:
        """Generate PDF using WeasyPrint from HTML."""
        from .html_generator import HTMLReportGenerator
        
        # Generate HTML first
        html_generator = HTMLReportGenerator()
        temp_html = output_path.parent / f"{output_path.stem}_temp.html"
        
        html_path = html_generator.generate_report(results, config, temp_html)
        
        # Convert HTML to PDF
        try:
            # Custom CSS for PDF
            pdf_css = CSS(string="""
                @page {
                    size: A4;
                    margin: 2cm;
                    @bottom-center {
                        content: "Page " counter(page) " of " counter(pages);
                        font-size: 10pt;
                        color: #666;
                    }
                }
                
                body { 
                    font-size: 10pt; 
                    line-height: 1.4; 
                }
                
                .header { 
                    page-break-inside: avoid; 
                    margin-bottom: 20pt;
                }
                
                .header h1 { 
                    font-size: 18pt; 
                    margin-bottom: 5pt; 
                }
                
                .summary-grid { 
                    display: flex; 
                    flex-wrap: wrap; 
                    justify-content: space-between; 
                    margin-bottom: 20pt; 
                }
                
                .summary-card { 
                    width: 30%; 
                    margin-bottom: 10pt; 
                    page-break-inside: avoid; 
                }
                
                .summary-card .value { 
                    font-size: 16pt; 
                }
                
                .chart-container { 
                    page-break-inside: avoid; 
                    margin: 20pt 0; 
                }
                
                .result-item { 
                    page-break-inside: avoid; 
                    margin-bottom: 15pt; 
                    border-left: 3pt solid #667eea; 
                    padding-left: 10pt; 
                }
                
                .result-header { 
                    margin-bottom: 10pt; 
                }
                
                .result-provider { 
                    font-weight: bold; 
                    font-size: 12pt; 
                }
                
                .assertion-results { 
                    display: flex; 
                    flex-wrap: wrap; 
                    gap: 5pt; 
                }
                
                .assertion { 
                    padding: 5pt; 
                    border-radius: 3pt; 
                    font-size: 8pt; 
                    margin-right: 5pt; 
                    margin-bottom: 5pt; 
                }
                
                .metadata { 
                    font-size: 8pt; 
                    color: #666; 
                    margin-top: 10pt; 
                    border-top: 1pt solid #eee; 
                    padding-top: 5pt; 
                }
                
                canvas { 
                    max-width: 100%; 
                    height: auto; 
                }
                
                @media print {
                    .chart-container canvas {
                        page-break-inside: avoid;
                    }
                }
            """)
            
            # Generate PDF
            output_path.parent.mkdir(parents=True, exist_ok=True)
            HTML(filename=str(html_path)).write_pdf(str(output_path), stylesheets=[pdf_css])
            
        finally:
            # Clean up temporary HTML file
            if temp_html.exists():
                temp_html.unlink()
        
        return output_path
    
    def _generate_with_reportlab(
        self,
        results: List[Dict[str, Any]],
        config: Dict[str, Any],
        output_path: Path
    ) -> Path:
        """Generate PDF using ReportLab."""
        # Calculate summary statistics
        summary = self._calculate_summary(results)
        
        # Create PDF document
        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=12
        )
        
        subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=styles['Heading3'],
            fontSize=12,
            spaceBefore=12,
            spaceAfter=6
        )
        
        # Build document content
        story = []
        
        # Title page
        story.append(Paragraph(config.get('description', 'LLM Evaluation Report'), title_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
        story.append(PageBreak())
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", heading_style))
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Tests', str(summary['total_tests'])],
            ['Success Rate', f"{summary['pass_rate']*100:.1f}%"],
            ['Average Score', f"{summary['average_score']:.3f}"],
            ['Total Cost', f"${summary['total_cost']:.4f}"],
            ['Average Latency', f"{summary['average_latency']*1000:.0f}ms"],
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Provider comparison chart (if multiple providers)
        provider_stats = self._calculate_provider_stats(results)
        if len(provider_stats) > 1:
            story.append(Paragraph("Provider Performance Comparison", heading_style))
            
            chart = self._create_provider_chart(provider_stats)
            story.append(chart)
            story.append(Spacer(1, 20))
        
        # Detailed Results
        story.append(Paragraph("Detailed Results", heading_style))
        
        for i, result in enumerate(results[:10]):  # Limit to first 10 results for PDF
            story.append(Paragraph(f"Test {i+1}: {result.get('provider', 'Unknown Provider')}", subheading_style))
            
            # Result details
            details = [
                f"Score: {result.get('score', 0):.3f}",
                f"Cost: ${result.get('cost', 0):.6f}",
                f"Latency: {(result.get('latency', 0)*1000):.0f}ms"
            ]
            
            if result.get('token_usage'):
                token_usage = result['token_usage']
                details.append(f"Tokens: {token_usage.get('total_tokens', 0)}")
            
            story.append(Paragraph(" | ".join(details), styles['Normal']))
            story.append(Spacer(1, 6))
            
            # Response preview
            response = result.get('response', '')
            if len(response) > 200:
                response = response[:200] + "..."
            
            story.append(Paragraph(f"<b>Response:</b> {response}", styles['Normal']))
            
            # Assertions
            if result.get('assertion_results'):
                assertion_summary = []
                for assertion in result['assertion_results']:
                    status = "✓" if assertion.get('passed', False) else "✗"
                    assertion_summary.append(f"{status} {assertion.get('type', 'Unknown')}")
                
                story.append(Paragraph(f"<b>Assertions:</b> {' | '.join(assertion_summary)}", styles['Normal']))
            
            story.append(Spacer(1, 12))
            
            # Add page break after every 3 results
            if (i + 1) % 3 == 0 and i < len(results) - 1:
                story.append(PageBreak())
        
        if len(results) > 10:
            story.append(Paragraph(f"... and {len(results) - 10} more results", styles['Normal']))
        
        # Build PDF
        doc.build(story)
        return output_path
    
    def _create_provider_chart(self, provider_stats: Dict[str, Dict[str, Any]]) -> Drawing:
        """Create a provider comparison chart for ReportLab."""
        drawing = Drawing(400, 200)
        
        # Create bar chart
        chart = VerticalBarChart()
        chart.x = 50
        chart.y = 50
        chart.height = 125
        chart.width = 300
        
        # Data for chart
        providers = list(provider_stats.keys())
        scores = [stats['average_score'] for stats in provider_stats.values()]
        
        chart.data = [scores]
        chart.categoryAxis.categoryNames = providers
        chart.valueAxis.valueMin = 0
        chart.valueAxis.valueMax = max(scores) * 1.1 if scores else 1
        
        # Styling
        chart.bars[0].fillColor = colors.lightblue
        chart.bars[0].strokeColor = colors.blue
        
        drawing.add(chart)
        return drawing
    
    def _calculate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics from results."""
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
        """Calculate per-provider statistics."""
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
    
    def generate_executive_summary(
        self,
        results: List[Dict[str, Any]],
        config: Dict[str, Any],
        output_path: Path
    ) -> Path:
        """Generate a concise executive summary PDF.
        
        Args:
            results: List of evaluation results
            config: Evaluation configuration
            output_path: Output file path
            
        Returns:
            Path to generated summary PDF
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required for executive summary generation")
        
        summary = self._calculate_summary(results)
        provider_stats = self._calculate_provider_stats(results)
        
        # Create PDF document
        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Title'],
            alignment=TA_CENTER,
            fontSize=20,
            spaceAfter=30
        )
        
        story = []
        
        # Title
        story.append(Paragraph("LLM Evaluation Executive Summary", title_style))
        story.append(Spacer(1, 12))
        
        # Key metrics
        story.append(Paragraph("Key Performance Indicators", styles['Heading2']))
        
        kpi_data = [
            ['Total Test Cases', str(summary['total_tests'])],
            ['Overall Success Rate', f"{summary['pass_rate']*100:.1f}%"],
            ['Average Quality Score', f"{summary['average_score']:.3f}"],
            ['Total API Cost', f"${summary['total_cost']:.4f}"],
            ['Average Response Time', f"{summary['average_latency']*1000:.0f}ms"],
        ]
        
        kpi_table = Table(kpi_data, colWidths=[3*inch, 2*inch])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(kpi_table)
        story.append(Spacer(1, 20))
        
        # Provider comparison (if applicable)
        if len(provider_stats) > 1:
            story.append(Paragraph("Provider Performance", styles['Heading2']))
            
            provider_data = [['Provider', 'Success Rate', 'Avg Score', 'Avg Cost', 'Avg Latency']]
            for provider, stats in provider_stats.items():
                provider_data.append([
                    provider,
                    f"{stats['pass_rate']*100:.1f}%",
                    f"{stats['average_score']:.3f}",
                    f"${stats['average_cost']:.4f}",
                    f"{stats['average_latency']*1000:.0f}ms"
                ])
            
            provider_table = Table(provider_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 1*inch])
            provider_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(provider_table)
        
        # Build PDF
        doc.build(story)
        return output_path