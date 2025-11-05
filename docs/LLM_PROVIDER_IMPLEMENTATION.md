# LLM Provider Implementation - Technical Documentation

## Overview

The Answer Sheet Marker now supports multiple LLM providers through a flexible abstraction layer, allowing users to choose between paid API services and free locally-hosted models.

## Architecture

### Design Patterns Used

1. **Strategy Pattern**: Different LLM providers implement the same interface
2. **Adapter Pattern**: Each provider adapts its specific API to our unified interface
3. **Factory Pattern**: `create_llm_client()` creates the appropriate provider based on configuration
4. **Dependency Injection**: Clients are injected into agents, making them provider-agnostic

### Components

```
src/answer_marker/llm/
├── __init__.py              # Package exports
├── base.py                  # Abstract base class (BaseLLMClient)
├── anthropic_adapter.py     # Anthropic Claude adapter
├── ollama_adapter.py        # Ollama local LLM adapter
├── openai_adapter.py        # OpenAI/compatible adapter
└── factory.py               # Factory for creating clients
```

---

## Base Interface (`base.py`)

###  `BaseLLMClient` Abstract Class

All LLM providers must implement:

```python
class BaseLLMClient(ABC):
    @abstractmethod
    def create_message(
        self,
        system: str,
        messages: List[Dict[str, Any]],
        max_tokens: int = 4096,
        temperature: float = 0.0,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> LLMResponse:
        """Create a message with the LLM."""
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        pass
```

### `LLMResponse` Dataclass

Unified response format:

```python
@dataclass
class LLMResponse:
    content: str                    # Text response
    stop_reason: StopReason         # Why generation stopped
    tool_uses: List[ToolUse]        # Tool/function calls
    usage: Optional[Dict[str, int]] # Token usage stats
```

---

## Providers Implemented

### 1. Anthropic Adapter (`anthropic_adapter.py`)

**Purpose**: Wraps Anthropic's Python SDK

**Key Features**:
- Direct integration with Anthropic API
- Native tool use support
- Token usage tracking
- Vision support (Sonnet/Opus)

**Usage**:
```python
client = AnthropicAdapter(
    model="claude-sonnet-4-5-20250929",
    api_key="sk-ant-..."
)
```

**Implementation Notes**:
- Maps Anthropic's stop reasons to our `StopReason` enum
- Extracts tool uses from content blocks
- Handles text and tool_use block types

---

### 2. Ollama Adapter (`ollama_adapter.py`)

**Purpose**: Local LLM support via Ollama

**Key Features**:
- HTTP API communication with local Ollama server
- Tool use via structured JSON prompting
- No API costs
- Privacy-preserving (fully local)

**Usage**:
```python
client = OllamaAdapter(
    model="llama3:70b",
    base_url="http://localhost:11434"
)
```

**Implementation Notes**:
- Converts tool definitions to JSON schema prompts
- Uses `format="json"` parameter for structured output
- Handles connection errors gracefully
- Includes `list_models()` for discovering available models

**Tool Use Strategy**:
Since Ollama models don't natively support function calling, we:
1. Convert tool schema to natural language description
2. Request JSON-formatted output
3. Parse the JSON response as tool input
4. Return as `ToolUse` object

---

### 3. OpenAI Adapter (`openai_adapter.py`)

**Purpose**: OpenAI and compatible APIs

**Key Features**:
- Works with OpenAI, Together.ai, and any OpenAI-compatible API
- Native function calling support
- Tiktoken integration for accurate token counting
- Vision support (GPT-4 Vision, GPT-4o)

**Usage**:
```python
# OpenAI
client = OpenAIAdapter(
    model="gpt-4-turbo",
    api_key="sk-..."
)

# Together.ai
client = OpenAIAdapter(
    model="meta-llama/Llama-3-70b-chat-hf",
    api_key="...",
    base_url="https://api.together.xyz/v1"
)
```

**Implementation Notes**:
- Converts Anthropic tool format to OpenAI function format
- Maps finish reasons to our stop reasons
- Uses tiktoken for accurate token counting
- Handles tool_calls from response

---

## Factory (`factory.py`)

### `create_llm_client()` Function

Creates the appropriate client based on provider string:

```python
client = create_llm_client(
    provider="ollama",          # or "anthropic", "openai", "together"
    model="llama3:70b",
    api_key=None,               # Not needed for Ollama
    base_url="http://localhost:11434"
)
```

### `LLMProvider` Enum

Supported providers:
- `ANTHROPIC`: Anthropic Claude
- `OLLAMA`: Local Ollama models
- `OPENAI`: OpenAI API
- `TOGETHER`: Together.ai (uses OpenAI adapter)

---

## Configuration Updates (`config.py`)

### New Settings

```python
class Settings(BaseSettings):
    # New unified LLM configuration
    llm_provider: str = "anthropic"
    llm_model: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None

    # Deprecated (backward compatibility)
    anthropic_api_key: Optional[str] = None
    claude_model: str = "claude-sonnet-4-5-20250929"
```

### `get_llm_config()` Method

Resolves configuration with backward compatibility:

```python
config = settings.get_llm_config()
# Returns:
# {
#     "provider": "ollama",
#     "model": "llama3",
#     "api_key": None,
#     "base_url": "http://localhost:11434",
#     "max_tokens": 8192,
#     "temperature": 0.0
# }
```

---

## Environment Variables

### New Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `LLM_PROVIDER` | Provider name | `ollama`, `anthropic`, `openai` |
| `LLM_MODEL` | Model identifier | `llama3:70b`, `gpt-4` |
| `LLM_API_KEY` | API key | `sk-...` |
| `LLM_BASE_URL` | Custom API endpoint | `http://localhost:11434` |

### Backward Compatibility

Old variables still work:
- `ANTHROPIC_API_KEY` → Used if `LLM_API_KEY` not set
- `CLAUDE_MODEL` → Used as default if `LLM_MODEL` not set

---

## Usage Examples

### Example 1: Using Ollama

```python
from answer_marker.llm import create_llm_client

# Create client
client = create_llm_client(
    provider="ollama",
    model="llama3",
    base_url="http://localhost:11434"
)

# Make a request
response = client.create_message(
    system="You are a helpful assistant.",
    messages=[
        {"role": "user", "content": "What is 2+2?"}
    ],
    max_tokens=1000,
    temperature=0.0
)

print(response.content)  # "4"
print(response.usage)    # {'input_tokens': 15, 'output_tokens': 3}
```

### Example 2: Switching Providers

```python
from answer_marker.config import settings
from answer_marker.llm import create_llm_client_from_config

# Configuration automatically selects provider
client = create_llm_client_from_config(settings)

# Works identically regardless of provider!
response = client.create_message(...)
```

### Example 3: Tool Use

```python
tools = [{
    "name": "evaluate_answer",
    "description": "Evaluate a student answer",
    "input_schema": {
        "type": "object",
        "properties": {
            "score": {"type": "number"},
            "feedback": {"type": "string"}
        },
        "required": ["score", "feedback"]
    }
}]

response = client.create_message(
    system="You are a grading assistant.",
    messages=[{"role": "user", "content": "Grade this answer: '2+2=4'"}],
    tools=tools,
    tool_choice={"type": "tool", "name": "evaluate_answer"}
)

# Check for tool use
if response.has_tool_use:
    tool_use = response.tool_uses[0]
    print(tool_use.name)   # "evaluate_answer"
    print(tool_use.input)  # {"score": 10, "feedback": "Correct!"}
```

---

## Testing

### Unit Tests

Each adapter should be tested independently:

```python
def test_ollama_adapter():
    client = OllamaAdapter(model="llama3")

    response = client.create_message(
        system="You are helpful",
        messages=[{"role": "user", "content": "Hi"}]
    )

    assert isinstance(response, LLMResponse)
    assert response.content
    assert response.stop_reason in [StopReason.END_TURN, StopReason.MAX_TOKENS]
```

### Integration Tests

Test provider switching:

```python
def test_provider_switching():
    providers = ["anthropic", "ollama", "openai"]

    for provider in providers:
        client = create_llm_client(provider, ...)
        response = client.create_message(...)
        assert response.content
```

---

## Performance Considerations

### Latency

| Provider | Typical Latency | Notes |
|----------|----------------|-------|
| Anthropic | 1-3s | Fast, API-based |
| OpenAI | 1-4s | Fast, API-based |
| Together.ai | 2-5s | Moderate, API-based |
| Ollama (local) | 5-30s | Depends on hardware |

### Throughput

| Provider | Concurrent Requests | Batch Size |
|----------|-------------------|-----------|
| Anthropic | 3-5 | 5-10 students |
| OpenAI | 3-5 | 5-10 students |
| Ollama | 1 | 1-3 students |

### Cost

| Provider | Per Student | Per 100 Students |
|----------|------------|------------------|
| Anthropic | $0.10-0.50 | $10-50 |
| OpenAI | $0.20-0.80 | $20-80 |
| Together.ai | $0.05-0.20 | $5-20 |
| Ollama | $0.00 | $0.00 |

---

## Future Enhancements

### Planned Features

1. **Caching Layer**: Cache responses for identical inputs
2. **Retry Logic**: Automatic retry with exponential backoff
3. **Rate Limiting**: Respect API rate limits
4. **Streaming Support**: Stream responses for long generations
5. **Additional Providers**:
   - Hugging Face Inference API
   - Azure OpenAI
   - Google PaLM/Gemini
   - Cohere

### Extensibility

Adding a new provider:

1. Create adapter class extending `BaseLLMClient`
2. Implement `create_message()` and `count_tokens()`
3. Add to `LLMProvider` enum
4. Add case to factory `create_llm_client()`
5. Document configuration
6. Add example `.env` file

---

## Best Practices

### For Developers

1. ✅ Always use the factory to create clients
2. ✅ Handle `LLMResponse` objects consistently
3. ✅ Test with multiple providers
4. ✅ Document provider-specific behavior
5. ✅ Use type hints

### For Users

1. ✅ Start with Ollama for development/testing
2. ✅ Use Anthropic/OpenAI for production
3. ✅ Set `TEMPERATURE=0.0` for consistency
4. ✅ Monitor token usage and costs
5. ✅ Keep sensitive data local when possible

---

## Troubleshooting

### Common Issues

**Issue**: `ImportError: No module named 'openai'`
```bash
# Solution: Install OpenAI support
poetry install -E llm
```

**Issue**: Ollama connection refused
```bash
# Solution: Start Ollama server
ollama serve
```

**Issue**: Different results from different providers
```bash
# Solution: Set temperature=0.0 for all providers
TEMPERATURE=0.0
```

---

## References

- Anthropic API: https://docs.anthropic.com/
- Ollama: https://ollama.com/
- OpenAI API: https://platform.openai.com/docs
- Together.ai: https://docs.together.ai/
