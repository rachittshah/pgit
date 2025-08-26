# Model Comparison Example

This example demonstrates how to compare different models on analytical tasks.

## Overview

This configuration compares GPT-3.5 Turbo and GPT-4o Mini on text analysis tasks. It tests the models' ability to:
- Provide structured analysis
- Extract key insights from business, workplace, and environmental scenarios
- Follow formatting instructions

## Configuration Features

- **Provider Configuration**: Uses detailed provider configs with labels and temperature settings
- **Complex Prompts**: Multi-line prompt with clear structure and expectations
- **Varied Test Cases**: Three different domains (financial, workplace, environmental)
- **Structure Validation**: Uses regex to ensure numbered list format
- **Content Validation**: Checks for domain-specific terminology

## Running the Example

1. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```

2. Run the evaluation:
   ```bash
   cd examples/model-comparison
   promptfoo-py eval --verbose
   ```

3. The `--verbose` flag will show detailed results for each test case.

## Expected Outcomes

- Both models should pass most tests
- GPT-4o Mini may provide more detailed and structured responses
- Cost differences will be visible (GPT-4 typically costs more)
- Response quality and structure adherence can be compared

## Analysis Points

After running, compare:
1. **Accuracy**: Which model better addresses the analysis focus?
2. **Structure**: Which model follows the numbered format more consistently?
3. **Cost-effectiveness**: Cost per token for each model
4. **Response time**: Latency differences between models