# LLM Judge Evaluation Example

This example demonstrates advanced evaluation techniques using LLMs as judges to assess the quality of AI responses beyond simple text matching.

## LLM-as-Judge Capabilities

### Available LLM-Based Assertions

1. **`llm-rubric`**: Custom scoring based on detailed criteria
2. **`llm-factcheck`**: Automated fact-checking of responses  
3. **`llm-helpfulness`**: Evaluation of response usefulness and clarity

### Why Use LLM Judges?

- **Nuanced Evaluation**: Understand context, tone, and quality beyond keywords
- **Flexible Criteria**: Define custom rubrics for your specific use case
- **Scalable Assessment**: Automate complex quality evaluations
- **Multi-dimensional Scoring**: Evaluate empathy, professionalism, accuracy simultaneously

## Running This Example

### Setup
```bash
# Required API keys
export OPENAI_API_KEY=your_openai_key
export ANTHROPIC_API_KEY=your_anthropic_key

cd examples/llm-judge
```

### Run Evaluation
```bash
llm-eval eval -c llmeval.yaml --verbose
```

## Test Scenarios

### 1. Frustrated Customer Handling
**Tests**: Empathy, professionalism, helpfulness, accountability

**Custom Rubric**:
- Empathy: Acknowledges customer frustration
- Professionalism: Appropriate and respectful tone
- Helpfulness: Offers concrete resolution steps
- Accountability: Takes responsibility without excuses

### 2. Return Policy Explanation
**Tests**: Clarity, completeness, actionability, factual accuracy

**Includes**: Automated fact-checking to verify policy information accuracy

### 3. Positive Feedback & Upselling
**Tests**: Appreciation, relevance, balance, information quality

**Evaluates**: How well the AI handles positive feedback and suggests additional products without being pushy

## Understanding Results

### LLM Rubric Scoring
```yaml
assert:
  - type: llm-rubric
    value: |
      Evaluate on scale 0-100 based on:
      1. Criterion 1 (25 points)
      2. Criterion 2 (25 points) 
      3. Criterion 3 (25 points)
      4. Criterion 4 (25 points)
      
      Score >= 70 indicates success
```

### Result Interpretation
- **Score**: 0.0-1.0 normalized from LLM judge's 0-100 rating
- **Passed**: Whether the response meets the rubric threshold
- **Message**: Detailed feedback from the judge LLM
- **Metadata**: Judge model used, costs, raw evaluation

## Judge Model Selection

The framework automatically selects appropriate judge models:
- **GPT-3.5 Turbo**: General rubric evaluation (fast, cost-effective)
- **GPT-4o Mini**: Fact-checking (better accuracy for factual claims)
- **Claude Sonnet**: Alternative judge option (can be configured)

## Benefits Over Traditional Assertions

| Traditional | LLM Judge |
|-------------|-----------|
| `contains: "sorry"` | Evaluates genuine empathy vs perfunctory apology |
| `regex: "[0-9]+ days"` | Understands if timeframe explanation is clear and appropriate |
| `not-contains: "bad"` | Assesses overall tone and professional communication style |
| Manual review needed | Automated quality assessment with detailed feedback |

## Customization Tips

1. **Write Specific Rubrics**: More detailed criteria yield better evaluations
2. **Set Appropriate Thresholds**: Calibrate score thresholds based on your quality standards  
3. **Combine Approaches**: Use both LLM judges and traditional assertions for comprehensive testing
4. **Monitor Judge Costs**: LLM evaluations add cost but provide much richer insights

This approach enables sophisticated quality assessment that scales with your evaluation needs while providing detailed, actionable feedback on AI response quality.