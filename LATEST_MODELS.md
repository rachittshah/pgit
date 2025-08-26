# Latest Supported Models (2024-2025)

This document provides an overview of the latest models supported by pgit's LiteLLM integration as of 2024-2025.

## 🚀 Major Provider Updates

### OpenAI Models
- **GPT-4o** - Most advanced multimodal model, faster and cheaper than GPT-4 Turbo
- **GPT-4o Mini** - Most cost-efficient model with vision capabilities
- **GPT-4.1**, **GPT-4.1 Mini**, **GPT-4.1 Nano** - New advanced models
- **O3**, **O3-Mini**, **O4-Mini** - Reasoning models
- **GPT Image-1** - Image generation model

### Anthropic Models  
- **Claude 3.5 Sonnet (20241022)** - Latest Claude 3.5 Sonnet with enhanced capabilities
- **Claude 4 Opus**, **Claude 4 Sonnet** - Next generation Claude models
- **Claude 3.5 Haiku (20241022)** - PDF input support

### Google Models
- **Gemini 2.5 Pro** - Advanced reasoning and multimodal capabilities
- **Gemini 2.5 Flash** - Fast and efficient model
- **Gemini 2.5 Pro Preview** - Preview versions with reasoning content
- **Gemini Flash 2** - Updated flash model
- **LearnLM** - Education-focused model

### DeepSeek Models
- **DeepSeek R1** - Advanced reasoning model with reasoning content support
- **DeepSeek V3** - Latest generation model  
- **DeepSeek Coder** - Specialized coding model

### Azure OpenAI
- **Azure GPT-4o** - Azure-hosted GPT-4o with EU/US region support
- **Azure Computer Use Preview** - Computer interaction capabilities
- **Azure GPT-4o Audio Preview** - Audio processing capabilities
- **Azure Phi-4** - Efficient small model

## 🏢 Provider-Specific Features

### Bedrock
- **Claude 4 Support** - Latest Anthropic models via Bedrock
- **Llama Vision Support** - Vision capabilities for Llama models
- **DeepSeek R1** - `us.deepseek.r1-v1:0` model support

### VertexAI
- **Imagen-4** - Latest image generation models
- **DeepSeek Integration** - DeepSeek models via Vertex AI
- **Enterprise Web Search** - Built-in search capabilities

### HuggingFace
- **Serverless Inference** - Support for multiple providers (Together AI, Fireworks, etc.)
- **DeepSeek R1 via Together AI** - `huggingface/together/deepseek-ai/DeepSeek-R1`
- **Enhanced Embedding Support** - Non-default input_type support

### Groq
- **Llama 3.1 Models** - Ultra-fast inference
- **Moonshotai/Kimi K2** - Chinese model support  
- **Qwen 3 32B** - High-quality Chinese model

### Mistral
- **Magistral Small/Medium** - New reasoning models
- **Mistral Large Latest** - Most capable model
- **Max Completion Tokens** - Enhanced parameter support

### Cohere
- **Command A-03-2025** - Latest command model
- **Embedding 3 Models** - Multimodal embedding support

### Novita AI
- **DeepSeek R1** - `novita/deepseek/deepseek-r1`
- **Llama 3.3 70B** - `novita/meta-llama/llama-3.3-70b-instruct`
- **Qwen 2.5 72B** - `novita/qwen/qwen-2.5-72b-instruct`

### Ollama
- **Wildcard Model Support** - Flexible model selection
- **JSON Schema Support** - Structured output generation

## 💰 Cost Tracking Updates

All new models include:
- ✅ Automatic cost calculation
- ✅ Token usage tracking  
- ✅ Multi-region pricing (EU/US for Azure)
- ✅ Batch API cost tracking
- ✅ Realtime API cost tracking

## 🔧 Configuration Examples

### Latest OpenAI Models
```yaml
provider: openai
model: gpt-4o  # or gpt-4.1, o3-mini
```

### Latest Anthropic Models  
```yaml
provider: anthropic
model: claude-3-5-sonnet-20241022  # or claude-4-opus
```

### Latest Google Models
```yaml
provider: google  
model: gemini-2.5-pro  # or gemini-2.5-flash
```

### DeepSeek R1 (Multiple Providers)
```yaml
# Direct DeepSeek API
provider: deepseek
model: deepseek-r1

# Via HuggingFace/Together AI
provider: huggingface
model: together/deepseek-ai/DeepSeek-R1

# Via Bedrock
provider: bedrock
model: us.deepseek.r1-v1:0
```

### Azure Models
```yaml
provider: azure
model: gpt-4o  # Auto-detects region pricing
```

## 🎯 Model Recommendations by Use Case

### **Code Generation**
1. **DeepSeek R1** - Best reasoning for complex problems
2. **Mistral Large Latest** - Excellent coding capabilities  
3. **GPT-4o** - Strong general coding performance

### **Creative Writing**
1. **Claude 3.5 Sonnet** - Superior creative capabilities
2. **GPT-4o** - Well-balanced creative performance
3. **Gemini 2.5 Pro** - Good for structured creativity

### **Fast Inference**
1. **Groq Llama 3.1 70B** - Ultra-fast processing
2. **GPT-4o Mini** - Fast and cost-effective
3. **Gemini 2.5 Flash** - Efficient processing

### **Document Analysis**
1. **Claude 3.5 Haiku** - PDF input support
2. **Azure GPT-4o** - Enterprise document processing
3. **Gemini 2.5 Pro** - Multimodal document understanding

### **Reasoning Tasks**
1. **DeepSeek R1** - Advanced reasoning content
2. **O3/O3-Mini** - Specialized reasoning models
3. **Magistral Medium** - Mistral's reasoning model

## 📊 Performance Characteristics

| Model | Speed | Cost | Reasoning | Multimodal | Context |
|-------|-------|------|-----------|------------|---------|
| GPT-4o | Fast | Medium | Excellent | Yes | 128K |
| Claude 3.5 Sonnet | Medium | High | Excellent | Yes | 200K |
| DeepSeek R1 | Medium | Low | Outstanding | No | 64K |
| Gemini 2.5 Pro | Fast | Medium | Good | Yes | 1M |
| Groq Llama 3.1 | Ultra-Fast | Low | Good | No | 70K |

## 🔄 Migration Guide

### Updating Existing Prompts
```yaml
# Old
model: gpt-4

# New  
model: gpt-4o
```

```yaml
# Old
model: claude-3-sonnet-20240229

# New
model: claude-3-5-sonnet-20241022
```

```yaml
# Old
model: gemini-pro

# New  
model: gemini-2.5-pro
```

## 🏗️ Future Roadmap

### Coming Soon
- **Claude 5** series models
- **GPT-5** when available
- **Gemini 3.0** models
- **Additional reasoning models** across providers
- **Enhanced multimodal capabilities**

---

*Last Updated: January 2025*  
*For the most current model availability, check the [LiteLLM documentation](https://docs.litellm.ai/)*