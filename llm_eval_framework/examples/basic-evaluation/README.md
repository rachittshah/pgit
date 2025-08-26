# Basic Evaluation Example

This example demonstrates the basic functionality of promptfoo-python.

## Configuration

The `promptfooconfig.yaml` file defines:
- Two OpenAI models to compare (gpt-3.5-turbo vs gpt-4o-mini)
- A simple prompt template with variable substitution
- Three test cases with different assertion types
- Default cost and latency thresholds

## Running the Example

1. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```

2. Run the evaluation:
   ```bash
   cd examples/basic-evaluation
   promptfoo-py eval
   ```

## Expected Output

The evaluation will:
1. Test both models against all three questions
2. Check that responses contain expected content
3. Verify cost and latency are within thresholds
4. Display a summary table with results

## Assertions Used

- `contains`: Checks if response contains specific text
- `not-contains`: Ensures response doesn't contain unwanted text
- `icontains`: Case-insensitive text matching
- `regex`: Pattern matching with regular expressions
- `cost`: Cost threshold validation
- `latency`: Response time validation