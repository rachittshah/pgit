# Multi-Provider LLM Comparison

This example demonstrates the universal provider support through LiteLLM integration, comparing responses across multiple AI providers simultaneously.

## Supported Providers

This configuration tests across 5 different providers:
- **OpenAI**: GPT-4, GPT-3.5 Turbo
- **Anthropic**: Claude 3 Sonnet
- **Google**: Gemini Pro  
- **Mistral**: Mistral Large

## Environment Setup

Set your API keys for the providers you want to test:

```bash
# Required for OpenAI models
export OPENAI_API_KEY=your_openai_key

# Required for Anthropic models  
export ANTHROPIC_API_KEY=your_anthropic_key

# Required for Google models
export GOOGLE_API_KEY=your_google_key

# Required for Mistral models
export MISTRAL_API_KEY=your_mistral_key
```

## Running the Evaluation

```bash
cd examples/multi-provider
llm-eval eval -c llmeval.yaml --verbose
```

## What This Tests

The configuration evaluates how different models explain technical concepts:

1. **Consistency**: All models should provide explanations under 100 words
2. **Quality**: Explanations should include practical examples
3. **Domain Knowledge**: Tests understanding of ML, blockchain, and API concepts
4. **Cost Efficiency**: Tracks cost across providers for budget optimization

## Expected Results

- **OpenAI GPT-4**: Highest quality, most expensive
- **GPT-3.5 Turbo**: Good balance of quality and cost
- **Claude 3 Sonnet**: Strong reasoning, good explanations
- **Gemini Pro**: Competitive performance, Google-specific strengths
- **Mistral Large**: European alternative with strong technical knowledge

## Analysis Points

After running, compare:
1. **Explanation Quality**: Which model provides the clearest explanations?
2. **Example Quality**: Which models give the most practical examples?
3. **Cost per Token**: Which provider offers the best value?
4. **Response Speed**: Latency differences between providers
5. **Domain Expertise**: Which models excel in specific technical areas?

This multi-provider approach lets you objectively compare AI models across multiple dimensions to make informed decisions about which provider best fits your specific use case.