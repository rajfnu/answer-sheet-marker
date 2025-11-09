# Google Gemini Setup Guide

## Overview

The Answer Sheet Marker now supports **Google Gemini 2.0 Flash** as a FREE alternative to paid LLM providers!

## What Was Changed

### 1. New Google Gemini Adapter
- Created `backend/src/answer_marker/llm/google_adapter.py`
- Implements full support for Gemini 2.0 Flash API
- Supports function calling, token counting, and streaming

### 2. Updated Factory
- Added `google` as a supported provider in `llm/factory.py`
- Updated LLMProvider enum to include `GOOGLE`

### 3. Dependencies
- Added `google-generativeai = "^0.8.0"` to `pyproject.toml`
- Installed via Poetry

### 4. Configuration
- Updated `.env` file to use Gemini by default
- Fixed `.env` file path resolution in `config.py`

## Configuration

Your `.env` file is now configured to use Google Gemini:

```bash
LLM_PROVIDER=google
LLM_MODEL=gemini-2.0-flash-exp
LLM_API_KEY=AIzaSyAfbXrb-aHSXT6BU2v2ay8SOOYAuMFMo2U
```

## Important: Environment Variables

**Note:** If you have `LLM_PROVIDER`, `LLM_MODEL`, or `LLM_API_KEY` set as environment variables in your shell, they will override the `.env` file values.

To ensure the `.env` file is used, either:

1. **Unset the environment variables** (temporary, for current session):
   ```bash
   unset LLM_PROVIDER LLM_MODEL LLM_API_KEY ANTHROPIC_API_KEY
   ```

2. **Remove from shell configuration** (permanent):
   Check and remove any LLM-related variables from:
   - `~/.zshrc`
   - `~/.bashrc`
   - `~/.bash_profile`
   - `~/.profile`

## Running the Application

### Option 1: Using Poetry (Recommended)
```bash
cd backend
poetry run answer-marker <command>
```

### Option 2: If Environment Variables Are Set
```bash
cd backend
env -u LLM_PROVIDER -u LLM_MODEL -u LLM_API_KEY poetry run answer-marker <command>
```

## Switching Between Providers

To switch between different LLM providers, simply update the `.env` file:

### Google Gemini (FREE)
```bash
LLM_PROVIDER=google
LLM_MODEL=gemini-2.0-flash-exp
LLM_API_KEY=YOUR_GOOGLE_API_KEY
```

### Anthropic Claude
```bash
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-5-20250929
LLM_API_KEY=YOUR_ANTHROPIC_API_KEY
```

### OpenAI GPT
```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
LLM_API_KEY=YOUR_OPENAI_API_KEY
```

### Local Ollama
```bash
LLM_PROVIDER=ollama
LLM_MODEL=llama3:70b
LLM_BASE_URL=http://localhost:11434
```

## Benefits of Gemini 2.0 Flash

- ✅ **FREE** (with usage limits)
- ✅ **Fast** response times
- ✅ **High quality** output
- ✅ **Function calling** support
- ✅ **Vision** capabilities
- ✅ **Large context** window

## API Key

Get your free Google API key from:
https://makersuite.google.com/app/apikey

## Testing

To verify Gemini is working:

```bash
cd backend
poetry run python -c "
from answer_marker.config import settings
config = settings.get_llm_config()
print(f'Provider: {config[\"provider\"]}')
print(f'Model: {config[\"model\"]}')
"
```

Expected output:
```
Provider: google
Model: gemini-2.0-flash-exp
```

## Troubleshooting

### Issue: Still using Anthropic instead of Gemini

**Cause:** Environment variables are overriding the `.env` file.

**Solution:**
```bash
# Check for environment variables
env | grep -E "LLM_|ANTHROPIC"

# If found, unset them
unset LLM_PROVIDER LLM_MODEL LLM_API_KEY ANTHROPIC_API_KEY

# Or run with env -u
env -u LLM_PROVIDER -u LLM_MODEL -u LLM_API_KEY poetry run answer-marker <command>
```

### Issue: "Google Generative AI package not installed"

**Solution:**
```bash
cd backend
poetry install
```

### Issue: API key invalid

**Solution:**
1. Verify your API key at https://makersuite.google.com/app/apikey
2. Update the `LLM_API_KEY` in `.env`
3. Ensure no quotes around the API key value

## Next Steps

Now that Gemini is configured, you can:
1. Run the marking workflow with the free Gemini API
2. Process answer sheets without API costs
3. Switch to other providers anytime by updating `.env`

## Support

For issues or questions:
- Check the logs in `./logs/app.log`
- Ensure your API key is valid
- Verify internet connection
- See the main README for general troubleshooting
