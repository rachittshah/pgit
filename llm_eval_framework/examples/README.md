# LLM Evaluation Framework Examples

This directory contains example configurations demonstrating various features of the LLM Evaluation Framework.

## Quick Start Examples

### 1. Basic Evaluation (`basic_example.yaml`)
```yaml
description: "Simple LLM evaluation example"
providers:
  - id: "gpt-3.5-turbo"
prompts:
  - "Answer this question: {{question}}"
tests:
  - vars:
      question: "What is 2+2?"
    assert:
      - type: "contains"
        value: "4"
```

Run with:
```bash
llm-eval eval -c examples/basic_example.yaml -o results.json
```

### 2. Multi-Provider Comparison (`provider_comparison.yaml`)
Compare multiple LLM providers on the same tasks:

```yaml
providers:
  - id: "gpt-4"
  - id: "gpt-3.5-turbo" 
  - id: "claude-3-sonnet"
  - id: "gemini-pro"

prompts:
  - "Explain {{concept}} in simple terms"

tests:
  - vars:
      concept: "machine learning"
    assert:
      - type: "llm-rubric"
        value:
          criteria: "Rate clarity and accuracy (1-5)"
```

### 3. Comprehensive Evaluation (`comprehensive_example.yaml`)
Full-featured example with:
- Multiple providers
- Various assertion types
- Multi-turn conversations  
- Custom evaluators
- Variable transformations
- Red team testing
- Report generation

## Feature Demonstrations

### Multi-turn Conversations
```yaml
conversation_tests:
  - description: "Customer support chat"
    system: "You are a helpful support agent"
    turns:
      - user: "I need help with installation"
        assert:
          - type: "contains"
            value: "help"
      - user: "It's not working on Windows"
        assert:
          - type: "conversation-context"
            value: ["Windows", "installation"]
```

### Custom Python Evaluators
```yaml
tests:
  - assert:
      - type: "python"
        value: |
          # Custom scoring logic
          word_count = len(output.split())
          has_examples = "example" in output.lower()
          
          score = 0.5
          if word_count > 50:
              score += 0.3
          if has_examples:
              score += 0.2
          
          result = score
```

### LLM-as-Judge Evaluation
```yaml
tests:
  - assert:
      - type: "llm-rubric"
        value:
          criteria: |
            Rate this response on:
            - Accuracy (1-5)
            - Helpfulness (1-5)
            - Clarity (1-5)
      - type: "llm-factcheck"
        value: "Verify factual accuracy of the response"
```

### Variable Transformations
```yaml
transforms:
  - type: "jinja2"
    template: "Question: {{question}} (Domain: {{domain}})"
    target: "formatted_input"
  
  - type: "python"
    code: |
      question_length = len(question.split())
      complexity = "high" if question_length > 10 else "low"
```

### Red Team Testing
```yaml
redteam:
  enabled: true
  plugins:
    - "prompt-injection"
    - "jailbreak"
    - "harmful-content"
  numTests: 100
```

## Dataset Examples

### CSV Dataset (`datasets/qa_dataset.csv`)
```csv
question,expected,domain
"What is the capital of France?","Paris","geography"
"What is 2+2?","4","math"
"Who wrote Romeo and Juliet?","Shakespeare","literature"
```

### JSON Dataset (`datasets/technical_questions.json`)
```json
{
  "test_cases": [
    {
      "vars": {
        "question": "How does HTTP work?",
        "domain": "networking"
      },
      "assert": [
        {"type": "contains", "value": "request"},
        {"type": "contains", "value": "response"}
      ]
    }
  ]
}
```

## Running Examples

### Basic Evaluation
```bash
# Run basic evaluation
llm-eval eval -c examples/basic_example.yaml

# Save results to file
llm-eval eval -c examples/basic_example.yaml -o results.json

# Generate HTML report
llm-eval eval -c examples/basic_example.yaml -o report.html --format html
```

### Advanced Analysis
```bash
# Run evaluation
llm-eval eval -c examples/comprehensive_example.yaml -o results.json

# Analyze results
llm-eval analyze -r results.json

# Generate detailed report
llm-eval report -r results.json -o report.html --format html

# Compare with baseline
llm-eval compare -b baseline.json -c results.json
```

### Configuration Validation
```bash
# Validate configuration
llm-eval validate -c examples/comprehensive_example.yaml

# List available providers
llm-eval list-providers

# Initialize new project
llm-eval init --directory my-llm-project
```

## Environment Setup

Create a `.env` file with your API keys:
```bash
# OpenAI
OPENAI_API_KEY=your_openai_key_here

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_key_here

# Google
GOOGLE_API_KEY=your_google_key_here

# Other providers supported by LiteLLM
# COHERE_API_KEY=your_cohere_key
# HUGGINGFACE_API_KEY=your_hf_key
# etc.
```

## Output Formats

### JSON Results
```json
{
  "total_tests": 10,
  "passed_tests": 8,
  "pass_rate": 0.8,
  "average_score": 0.75,
  "results": [...]
}
```

### HTML Reports
Rich interactive reports with:
- Performance summary
- Provider comparison charts
- Detailed test results
- Cost and latency analysis

### PDF Reports
Professional reports for sharing:
- Executive summary
- Key metrics
- Detailed results
- Recommendations

## Best Practices

1. **Start Simple**: Begin with basic examples and gradually add complexity
2. **Use Meaningful Assertions**: Choose assertions that validate what you care about
3. **Leverage LLM Judges**: Use `llm-rubric` for subjective quality assessment
4. **Test Multiple Providers**: Compare different models for your use case
5. **Monitor Costs**: Use cost assertions to prevent expensive tests
6. **Organize Tests**: Group related tests and use descriptive names
7. **Version Control**: Keep your configurations in version control
8. **Regular Evaluation**: Set up automated evaluations for continuous monitoring

## Troubleshooting

### Common Issues

**API Key Missing**
```bash
Error: API key not found for provider 'gpt-4'
```
Solution: Set the appropriate environment variable (e.g., `OPENAI_API_KEY`)

**Timeout Errors**
```bash
Error: Request timed out after 30 seconds
```
Solution: Increase timeout in configuration or use faster models

**Rate Limits**
```bash
Error: Rate limit exceeded
```
Solution: Reduce concurrency or add delays between requests

### Getting Help

- Check the configuration validation: `llm-eval validate`
- Review logs for detailed error messages
- Use verbose mode: `llm-eval eval --verbose`
- Check provider status: `llm-eval list-providers`

## Contributing

Found an issue with an example or want to contribute a new one?
1. Fork the repository
2. Create your example
3. Add documentation
4. Submit a pull request