# LLM Evaluation Framework - Advanced AI Testing Platform

A comprehensive Python framework for testing and evaluating Large Language Model applications with universal provider support. This project provides a declarative, YAML-based framework for prompt testing, model comparison, red teaming, and agent validation across 100+ AI providers via LiteLLM.

## 🚀 Key Features

- 🔧 **YAML-based Configuration**: Simple declarative configs for complex testing scenarios
- 🤖 **Universal Provider Support**: Test across 100+ providers via LiteLLM (OpenAI, Anthropic, Google, Azure, and more)
- 🎯 **Advanced Assertions**: Cost, latency, content-based, and LLM-graded evaluations
- 🛡️ **Red Teaming**: Built-in adversarial testing with jailbreak and injection strategies
- 💬 **Multi-turn Conversations**: Test dialogue systems and conversational AI
- 📊 **Professional Reporting**: HTML/PDF reports with charts and analytics
- ⚡ **Async Execution**: Fast concurrent testing across multiple providers
- 🧠 **AI-Powered Insights**: Automated performance analysis and recommendations
- 🛠️ **Custom Evaluators**: Python/JavaScript code for specialized testing
- 📈 **Advanced Analytics**: Comprehensive metrics and trend analysis

## 📋 Quick Start

```bash
# Install LLM Evaluation Framework
pip install llm-eval-framework

# Initialize a new evaluation project
llm-eval init

# Run evaluations
llm-eval eval

# Generate professional reports
llm-eval report -r results.json --format html
```

## ⚙️ Configuration

Create a `llmeval.yaml` file:

```yaml
description: "My AI evaluation"

providers:
  - id: "gpt-4"
    config:
      model: "gpt-4"
      temperature: 0.7
  - id: "claude-3-sonnet"
    config:
      model: "claude-3-sonnet-20240229"
      temperature: 0.7

prompts:
  - "Answer this question: {{question}}"

tests:
  - vars:
      question: "What is 2+2?"
    assert:
      - type: contains
        value: "4"
      - type: cost
        threshold: 0.01
      - type: llm-rubric
        value:
          criteria: "Rate the accuracy and clarity (1-5)"
```

## 🛡️ Red Teaming

Test your AI system's robustness:

```yaml
redteam:
  enabled: true
  plugins:
    - "harmful-content"
    - "prompt-injection" 
    - "jailbreak"
  strategies:
    - "iterative"
    - "multilingual"
  numTests: 100
```

## 💬 Multi-turn Conversations

Test dialogue systems:

```yaml
conversation_tests:
  - description: "Customer support conversation"
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
```

## 📦 Installation

### Basic Installation
```bash
pip install llm-eval-framework
```

### With All Features
```bash
pip install llm-eval-framework[full]
```

### Development Installation
```bash
git clone https://github.com/your-username/llm-eval-framework
cd llm-eval-framework
pip install -e .[dev]
```

## 🖥️ CLI Commands

```bash
# Initialize project
llm-eval init

# Run evaluations
llm-eval eval

# Run with specific config
llm-eval eval -c custom-config.yaml

# Generate HTML report
llm-eval report -r results.json --format html

# Generate PDF report  
llm-eval report -r results.json --format pdf

# Analyze results with insights
llm-eval analyze -r results.json

# Compare evaluations
llm-eval compare -b baseline.json -c current.json

# Validate configuration
llm-eval validate -c config.yaml

# List available providers
llm-eval list-providers
```

## 📊 Supported Providers (100+)

### Major Cloud Providers
- **OpenAI**: GPT-4, GPT-3.5-turbo, GPT-4-turbo
- **Anthropic**: Claude-3 (Opus, Sonnet, Haiku)
- **Google**: Gemini Pro, Gemini Ultra, PaLM
- **Azure**: Azure OpenAI deployments
- **AWS**: Bedrock models (Claude, Titan, etc.)

### Open Source & Local
- **Hugging Face**: Transformers models
- **Ollama**: Local model serving
- **Together AI**: Open source models
- **Replicate**: Cloud GPU inference

### Specialized Providers
- **Cohere**: Command, Generate models
- **AI21**: Jurassic models
- **Mistral**: Mistral 7B, Mixtral
- **And 80+ more via LiteLLM**

## 📈 Advanced Features

### Professional Reporting
- Interactive HTML reports with charts
- Executive PDF summaries
- Cost and performance analysis
- Provider comparison matrices

### Analytics & Insights
- Automated performance insights
- Statistical analysis and trends  
- Cost optimization recommendations
- Quality assessment metrics

### Custom Evaluators
```yaml
tests:
  - assert:
      - type: "python"
        value: |
          # Custom Python evaluation logic
          word_count = len(output.split())
          has_examples = "example" in output.lower()
          
          score = 0.5
          if word_count > 50: score += 0.3
          if has_examples: score += 0.2
          
          result = score
```

## 🏗️ Architecture

```
llm_eval/
├── config/          # Configuration handling
├── providers/       # LLM provider integrations  
├── evaluation/      # Core evaluation engine
├── redteam/         # Red teaming framework
├── conversation/    # Multi-turn dialogue support
├── analytics/       # Advanced metrics & insights
├── reporting/       # HTML/PDF report generation
├── transforms/      # Variable preprocessing
├── datasets/        # Dataset management
├── cli/             # Command-line interface
└── web/             # Results visualization
```

## 🧪 Examples

Check out the `examples/` directory:

- `basic-evaluation/` - Simple prompt testing
- `model-comparison/` - Multi-model comparison
- `conversation-testing/` - Multi-turn dialogue evaluation
- `advanced-analytics/` - Comprehensive analysis
- `custom-evaluators/` - Python/JS custom logic

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`pytest`)
6. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

This is a proprietary, comprehensive evaluation framework designed for enterprise AI testing with advanced features including universal provider support, multi-turn conversations, automated insights, and professional reporting.

## 🔗 Key Technologies

- [LiteLLM](https://github.com/berriai/litellm) - Unified interface for 100+ LLM providers
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework for APIs
- [Pydantic](https://pydantic.dev/) - Data validation and settings management

---

**Star ⭐ this project if you find it useful!**