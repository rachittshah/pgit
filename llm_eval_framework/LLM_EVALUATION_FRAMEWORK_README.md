# 🚀 LLM Evaluation Framework - Complete Implementation

A comprehensive Python framework for evaluating Large Language Model applications with universal provider support. This advanced framework provides declarative, YAML-based evaluation with professional reporting, analytics, and enterprise-grade features.

## 🌟 **Enterprise-Grade Features**

### 🤖 **Universal Provider Support (100+)**
- **OpenAI**: GPT-4, GPT-3.5-turbo, GPT-4-turbo, o1-preview
- **Anthropic**: Claude-3 (Opus, Sonnet, Haiku), Claude-3.5-sonnet
- **Google**: Gemini Pro, Gemini Ultra, PaLM-2, Gemini-1.5
- **Azure**: All Azure OpenAI deployments
- **AWS Bedrock**: Claude, Titan, Cohere Command
- **Meta**: Llama models via various providers
- **Mistral**: 7B, 8x7B, 8x22B models
- **And 85+ more via LiteLLM integration**

### 📊 **Advanced Analytics & Reporting**
- **Interactive HTML Reports**: Chart.js visualizations with responsive design
- **Executive PDF Summaries**: WeasyPrint/ReportLab professional documents
- **Real-time Analytics**: Cost optimization insights and performance trends
- **Provider Benchmarking**: Comprehensive cross-model comparison matrices
- **Statistical Analysis**: Standard deviations, confidence intervals, trend analysis

### 🛠️ **Evaluation Capabilities**
- **Multi-turn Conversations**: Complete dialogue system testing
- **Custom Evaluators**: Python/JavaScript code execution
- **LLM-as-Judge**: GPT-4 powered quality assessment
- **Red Team Testing**: Adversarial prompt injection detection
- **Cost & Latency Monitoring**: Real-time performance optimization
- **Dataset Management**: CSV/JSON/YAML support with transformations

## 📋 **Quick Start**

### Installation
```bash
cd llm_eval_framework
pip install -r requirements.txt

# Or install with all features
pip install -r requirements-full.txt
```

### Basic Usage
```bash
# Initialize project
python -m llm_eval.cli.main init

# Run evaluation
python -m llm_eval.cli.main eval -c config.yaml

# Generate reports
python -m llm_eval.cli.main report -r results.json --format html

# Analyze results
python -m llm_eval.cli.main analyze -r results.json

# Compare evaluations
python -m llm_eval.cli.main compare -b baseline.json -c current.json
```

### Web Dashboard
```bash
# Start web UI with sample data
python demo_ui.py

# Visit: http://localhost:8081
```

## ⚙️ **Configuration Example**

Create `llmeval.yaml`:

```yaml
description: "Comprehensive LLM Evaluation"

providers:
  - id: "gpt-4"
    config:
      model: "gpt-4"
      temperature: 0.7
      max_tokens: 1000
  
  - id: "claude-3-sonnet"
    config:
      model: "claude-3-sonnet-20240229"
      temperature: 0.7
      max_tokens: 1000

prompts:
  - "You are a helpful assistant. Answer: {{question}}"
  - "As an expert in {{domain}}, explain: {{question}}"

tests:
  - description: "Basic Q&A Testing"
    vars:
      question: "What is machine learning?"
      domain: "AI"
    assert:
      - type: "contains"
        value: "algorithm"
      - type: "llm-rubric"
        value:
          criteria: "Rate accuracy and clarity (1-5)"
      - type: "cost"
        threshold: 0.01
      - type: "latency"
        threshold: 5.0

# Multi-turn conversation testing
conversation_tests:
  - description: "Customer support dialogue"
    system: "You are a helpful customer support agent."
    turns:
      - user: "I need help with my order"
        assert:
          - type: "contains"
            value: "help"
      - user: "Order #12345 is delayed"
        assert:
          - type: "conversation-context"
            value: ["order", "12345"]

# Red team testing
redteam:
  enabled: true
  plugins:
    - "prompt-injection"
    - "jailbreak"
    - "harmful-content"
  numTests: 50

# Advanced features
transforms:
  - type: "jinja2"
    template: "Question: {{question}} (Domain: {{domain}})"
    target: "formatted_prompt"

datasets:
  - path: "./datasets/qa_dataset.csv"
  - path: "./datasets/technical_questions.json"

reports:
  html:
    enabled: true
    path: "./reports/evaluation_report.html"
  pdf:
    enabled: true
    path: "./reports/executive_summary.pdf"
```

## 🏗️ **Architecture**

```
llm_eval/
├── analytics/          # Advanced metrics & insights engine
├── cli/               # Rich CLI interface with progress bars
├── config/            # YAML configuration system
├── conversation/      # Multi-turn dialogue management
├── datasets/          # CSV/JSON/YAML dataset loading
├── evaluation/        # Core evaluation engine
│   ├── assertions/    # Comprehensive assertion library
│   ├── evaluator.py   # Main evaluation orchestrator
│   └── streaming.py   # Real-time evaluation support
├── providers/         # Universal LLM provider system
│   ├── base.py        # Provider interface
│   ├── litellm_provider.py  # 100+ model support
│   └── registry.py    # Provider management
├── redteam/          # Adversarial testing framework
├── reporting/        # Professional report generation
│   ├── html_generator.py   # Interactive HTML reports
│   └── pdf_generator.py    # Executive PDF summaries
├── transforms/       # Variable preprocessing pipeline
└── web/             # FastAPI dashboard + sharing
    ├── app.py       # Main web application
    └── templates/   # Jinja2 templates
```

## 📊 **Professional Reporting**

### HTML Reports
- **Interactive Charts**: Provider comparison, cost analysis, performance trends
- **Responsive Design**: Mobile-friendly with modern UI
- **Detailed Results**: Full test breakdown with assertion analysis
- **Export Capabilities**: JSON/CSV export with one click

### PDF Reports
- **Executive Summaries**: Business-ready professional documents
- **Performance Metrics**: Key indicators with visual representations
- **Recommendations**: AI-powered insights for optimization
- **Custom Branding**: Professional layout with charts and tables

## 🚀 **Production Ready**

### Enterprise Features
- **Concurrent Processing**: Async evaluation across multiple providers
- **Error Handling**: Comprehensive retry logic and graceful failures  
- **Audit Trails**: Complete evaluation history and metadata
- **Cost Optimization**: Real-time spend tracking and alerts
- **Security**: Safe code execution with sandboxed evaluators

### Integration Ready
- **REST API**: FastAPI-based web service
- **CLI Interface**: Rich terminal experience with progress bars
- **Docker Support**: Containerized deployment ready
- **CI/CD Integration**: Automated evaluation pipelines
- **Monitoring**: Prometheus-compatible metrics

---

## 🚀 **Implementation Summary**

This comprehensive LLM evaluation framework represents a complete enterprise-grade solution for AI model testing and validation. Built with production reliability, professional reporting, and universal provider support.

**Key Metrics:**
- 📦 **15+ modules** with comprehensive functionality
- 🤖 **100+ LLM providers** supported via LiteLLM
- 📊 **Professional reporting** with HTML/PDF generation
- 🌐 **Web dashboard** with real-time analytics
- ⚡ **High performance** async concurrent processing
- 🛡️ **Enterprise security** with sandboxed execution

Ready for immediate deployment and production use.

---

🤖 **Generated with [Claude Code](https://claude.ai/code)**

Co-Authored-By: Claude <noreply@anthropic.com>