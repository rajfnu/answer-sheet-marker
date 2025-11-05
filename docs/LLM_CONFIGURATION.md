# LLM Configuration Guide

The Answer Sheet Marker system supports multiple LLM providers, allowing you to choose between API-based services or locally-hosted models.

## Supported Providers

### 1. **Anthropic Claude** (API-based, Paid)
- **Best for**: Highest quality, most reliable
- **Cost**: Pay per token
- **Models**: Claude Sonnet 4.5, Claude Opus, Claude Haiku
- **Setup time**: 2 minutes

### 2. **Ollama** (Local, Free)
- **Best for**: Privacy, no API costs, offline use
- **Cost**: Free (hardware costs only)
- **Models**: Llama 3, Mistral, Phi-3, many others
- **Setup time**: 10 minutes

### 3. **OpenAI** (API-based, Paid)
- **Best for**: GPT-4 access
- **Cost**: Pay per token
- **Models**: GPT-4, GPT-3.5-turbo
- **Setup time**: 2 minutes

### 4. **Together.ai** (API-based, Affordable)
- **Best for**: Cost-effective access to open models
- **Cost**: Lower than OpenAI/Anthropic
- **Models**: Llama 3 70B, Mixtral, many others
- **Setup time**: 5 minutes

---

## Quick Start Guides

### Option 1: Anthropic Claude (Recommended)

**Step 1:** Get API key from https://console.anthropic.com/

**Step 2:** Configure `.env`:
```bash
# LLM Provider Configuration
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-5-20250929
LLM_API_KEY=sk-ant-your-api-key-here

# Processing settings
MAX_TOKENS=8192
TEMPERATURE=0.0
```

**Step 3:** Run:
```bash
poetry run answer-marker mark -g marking_guide.pdf -a answers/
```

**Cost estimate**: $0.10-0.50 per student (depending on answer length)

---

### Option 2: Ollama (Free, Local)

**Step 1:** Install Ollama
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Download from https://ollama.com/download
```

**Step 2:** Start Ollama and download a model
```bash
# Start Ollama service
ollama serve

# In another terminal, download a model
ollama pull llama3:70b  # 40GB - Best quality
# OR
ollama pull llama3      # 4.7GB - Faster, still good
# OR
ollama pull mistral     # 4.1GB - Fast and efficient
```

**Step 3:** Configure `.env`:
```bash
# LLM Provider Configuration
LLM_PROVIDER=ollama
LLM_MODEL=llama3:70b
LLM_BASE_URL=http://localhost:11434

# Processing settings
MAX_TOKENS=8192
TEMPERATURE=0.0
```

**Step 4:** Run:
```bash
poetry run answer-marker mark -g marking_guide.pdf -a answers/
```

**Cost**: $0 (Free!)

---

### Option 3: OpenAI

**Step 1:** Get API key from https://platform.openai.com/api-keys

**Step 2:** Configure `.env`:
```bash
# LLM Provider Configuration
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
LLM_API_KEY=sk-your-openai-api-key

# Processing settings
MAX_TOKENS=8192
TEMPERATURE=0.0
```

---

### Option 4: Together.ai (Affordable API)

**Step 1:** Get API key from https://api.together.xyz/

**Step 2:** Configure `.env`:
```bash
# LLM Provider Configuration
LLM_PROVIDER=together
LLM_MODEL=meta-llama/Llama-3-70b-chat-hf
LLM_API_KEY=your-together-api-key
LLM_BASE_URL=https://api.together.xyz/v1

# Processing settings
MAX_TOKENS=8192
TEMPERATURE=0.0
```

---

## Recommended Models by Provider

### Anthropic Claude
| Model | Best For | Speed | Quality | Cost |
|-------|----------|-------|---------|------|
| `claude-sonnet-4-5-20250929` | Production use | Fast | Excellent | Medium |
| `claude-opus-4-20250514` | Highest quality | Slow | Best | High |
| `claude-haiku-4-20250315` | High volume | Very Fast | Good | Low |

### Ollama (Local)
| Model | Size | RAM Required | Quality | Speed |
|-------|------|--------------|---------|-------|
| `llama3:70b` | 40GB | 64GB | Excellent | Slow |
| `llama3` | 4.7GB | 8GB | Good | Fast |
| `mistral` | 4.1GB | 8GB | Good | Very Fast |
| `phi3:medium` | 7.9GB | 16GB | Good | Fast |

### OpenAI
| Model | Best For | Speed | Quality | Cost |
|-------|----------|-------|---------|------|
| `gpt-4-turbo` | Production | Fast | Excellent | High |
| `gpt-4` | Highest quality | Slow | Excellent | Very High |
| `gpt-3.5-turbo` | Testing | Very Fast | Good | Low |

### Together.ai
| Model | Best For | Speed | Quality | Cost |
|-------|----------|-------|---------|------|
| `meta-llama/Llama-3-70b-chat-hf` | Production | Fast | Excellent | Low |
| `mistralai/Mixtral-8x7B-Instruct-v0.1` | Balance | Fast | Very Good | Low |

---

## Performance Comparison

| Provider | Setup Time | Cost/Student | Quality | Privacy | Offline |
|----------|------------|--------------|---------|---------|---------|
| Anthropic | 2 min | $0.10-0.50 | ⭐⭐⭐⭐⭐ | ❌ | ❌ |
| Ollama | 10 min | $0.00 | ⭐⭐⭐⭐ | ✅ | ✅ |
| OpenAI | 2 min | $0.20-0.80 | ⭐⭐⭐⭐ | ❌ | ❌ |
| Together.ai | 5 min | $0.05-0.20 | ⭐⭐⭐⭐ | ❌ | ❌ |

---

## Troubleshooting

### Ollama Issues

**Problem**: "Could not connect to Ollama"
```bash
# Solution: Start Ollama service
ollama serve
```

**Problem**: "Model not found"
```bash
# Solution: Download the model
ollama pull llama3
```

**Problem**: Slow performance
```bash
# Solution: Use a smaller model or add more RAM
ollama pull mistral  # Faster, smaller model
```

### API Issues

**Problem**: "Credit balance too low"
- **Solution**: Add credits to your API account

**Problem**: Rate limit errors
- **Solution**: Reduce `MAX_CONCURRENT_REQUESTS` in `.env`

**Problem**: Timeout errors
- **Solution**: Increase timeout or use a faster model

---

## Advanced Configuration

### Custom API Endpoints

You can use any OpenAI-compatible API:

```bash
LLM_PROVIDER=openai
LLM_MODEL=your-model-name
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://your-api-endpoint.com/v1
```

### Model-Specific Parameters

```bash
# Adjust token limit
MAX_TOKENS=4096  # Reduce for faster responses

# Adjust temperature
TEMPERATURE=0.1  # Slightly more varied responses

# Concurrent processing
MAX_CONCURRENT_REQUESTS=5  # More parallel requests
BATCH_SIZE=10  # Process more students at once
```

---

## Cost Optimization

### For API-based Providers

1. **Use appropriate models**: Don't use Claude Opus for simple assessments
2. **Batch processing**: Process multiple students together
3. **Caching**: Enable caching to avoid redundant API calls
4. **Token limits**: Reduce `MAX_TOKENS` if possible

### For Local Providers

1. **Hardware**: More RAM = better performance
2. **Model size**: Smaller models are faster
3. **GPU**: Use GPU acceleration if available
4. **Quantization**: Use quantized models (e.g., `llama3:q4_0`)

---

## Switching Providers

To switch providers, simply update your `.env` file:

```bash
# From Anthropic to Ollama
LLM_PROVIDER=ollama
LLM_MODEL=llama3:70b
# Remove: LLM_API_KEY (not needed for Ollama)
```

No code changes required! The system automatically adapts.

---

## Best Practices

### For Production Use
✅ Use Anthropic Claude Sonnet or OpenAI GPT-4 Turbo
✅ Set `TEMPERATURE=0.0` for consistency
✅ Enable caching
✅ Monitor API costs
✅ Set up error handling and retries

### For Development/Testing
✅ Use Ollama with smaller models
✅ Use Anthropic Haiku or OpenAI GPT-3.5 for cost savings
✅ Test with smaller batches first
✅ Enable debug logging

### For Privacy-Sensitive Data
✅ Use Ollama (fully local)
✅ Ensure no data leaves your network
✅ Consider hardware requirements
✅ Plan for longer processing times

---

## Need Help?

- Check the main README for system requirements
- Review logs in `./logs/app.log`
- Open an issue on GitHub
- Check Ollama documentation: https://ollama.com/docs
