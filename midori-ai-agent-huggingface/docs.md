# midori-ai-agent-huggingface Documentation

Hugging Face local inference implementation of the Midori AI agent protocol.

## Overview

This package provides a fully local LLM inference backend using HuggingFace's transformers library. It implements the `MidoriAiAgentProtocol` interface, allowing it to be used interchangeably with other backends like `midori-ai-agent-openai` or `midori-ai-agent-langchain`.

**Key Benefits:**
- No external server required (unlike Ollama, LocalAI, vLLM)
- Fully offline capable (after model download)
- Same interface as other Midori AI agent backends
- 100% async-friendly using thread executors

## Usage

### Direct Usage

```python
from midori_ai_agent_huggingface import HuggingFaceLocalAgent
from midori_ai_agent_base import AgentPayload

# Create agent with a local model
agent = HuggingFaceLocalAgent(
    model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    device="auto",  # auto-detect GPU/CPU
    max_new_tokens=512,
    temperature=0.7,
)

# Create payload
payload = AgentPayload(
    user_message="Hello, how are you?",
    thinking_blob="",
    system_context="You are a helpful assistant.",
    user_profile={},
    tools_available=[],
    session_id="session-123",
)

# Invoke the agent
response = await agent.invoke(payload)
print(response.response)

# When done, unload the model to free memory
await agent.unload_model()
```

### Streaming Support

The adapter now supports streaming responses for real-time token generation:

```python
# Stream tokens as they are generated
async for token in agent.stream(payload):
    print(token, end="", flush=True)
```

### Factory Integration

```python
from midori_ai_agent_base import get_agent

# Use via factory (requires midori-ai-agent-huggingface to be installed)
agent = await get_agent(
    backend="huggingface",
    model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    api_key="",  # Not needed for local models
    device="cuda",
)

response = await agent.invoke(payload)
```

### Configuration File

```toml
# config.toml
[midori_ai_agent_base]
backend = "huggingface"
model = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

[midori_ai_agent_base.huggingface]
device = "auto"
torch_dtype = "auto"
max_new_tokens = 512
temperature = 0.7
```

Then load from config:
```python
from midori_ai_agent_base import get_agent_from_config

agent = await get_agent_from_config(config_path="config.toml")
```

## Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | str | required | HuggingFace model identifier |
| `device` | str | "auto" | Device: "auto", "cpu", "cuda", "mps" |
| `torch_dtype` | str | "auto" | Data type: "auto", "float16", "float32", "bfloat16" |
| `max_new_tokens` | int | 512 | Maximum tokens to generate |
| `temperature` | float | 0.7 | Sampling temperature (0.0-2.0) |
| `top_p` | float | 0.9 | Nucleus sampling probability |
| `top_k` | int | 50 | Top-k sampling parameter |
| `do_sample` | bool | True | Use sampling vs greedy decoding |
| `context_window` | int | 4096 | Maximum context size |
| `trust_remote_code` | bool | False | Trust remote code in model files |
| `load_in_8bit` | bool | False | Use 8-bit quantization |
| `load_in_4bit` | bool | False | Use 4-bit quantization |

## Recommended Models

### Small (Testing)
- `TinyLlama/TinyLlama-1.1B-Chat-v1.0` (~2GB) - Fast, good for testing

### Medium (Development)
- `microsoft/phi-2` (~5GB) - Good quality, reasonable size
- `Qwen/Qwen2.5-3B-Instruct` (~6GB) - Strong multilingual support

### Large (Production)
- `meta-llama/Llama-2-7b-chat-hf` (~14GB) - High quality
- `mistralai/Mistral-7B-Instruct-v0.2` (~14GB) - Excellent performance

## Memory Management

### Lazy Loading
Models are loaded on first inference, not at initialization. This means:
1. Creating an agent is instant
2. First inference includes model download/load time
3. Subsequent inferences are fast

### Unloading
Call `await agent.unload_model()` when done to free GPU/CPU memory:

```python
agent = HuggingFaceLocalAgent(model="...")
response = await agent.invoke(payload)

# Free memory
await agent.unload_model()
```

### Reference Counting
The pipeline manager uses reference counting for thread-safe model lifecycle management. Multiple concurrent requests can share the same loaded model, and the model is only unloaded when all references are released.

### Quantization
For reduced memory usage, enable quantization:

```python
# 8-bit (requires bitsandbytes)
agent = HuggingFaceLocalAgent(
    model="meta-llama/Llama-2-7b-chat-hf",
    load_in_8bit=True,
)

# 4-bit (requires bitsandbytes)
agent = HuggingFaceLocalAgent(
    model="meta-llama/Llama-2-7b-chat-hf",
    load_in_4bit=True,
)
```

## Memory History

The adapter supports conversation history via the `memory` field in `AgentPayload`:

```python
from midori_ai_agent_base import AgentPayload, MemoryEntryData

memory = [
    MemoryEntryData(role="user", content="My name is Alice"),
    MemoryEntryData(role="assistant", content="Hello Alice!"),
]

payload = AgentPayload(
    user_message="What is my name?",
    thinking_blob="",
    system_context="You are helpful.",
    user_profile={},
    tools_available=[],
    session_id="session-123",
    memory=memory,
)
```

## Tool Support

The adapter supports tool-call parsing from model output. Tools are described in the prompt and the model can indicate tool usage in two formats:

### Tool Call Formats

**JSON Format:**
```json
{"tool_calls": [{"name": "search", "arguments": {"query": "example"}}]}
```

**Text Format:**
```
TOOL_CALL: search(query=example, limit=10)
```

### Usage Example

```python
def search(query: str) -> str:
    """Search for information."""
    return f"Results for: {query}"

response = await agent.invoke_with_tools(payload, tools=[search])

# Check if tool calls were detected
if response.tool_calls:
    for call in response.tool_calls:
        print(f"Tool: {call['name']}, Args: {call['arguments']}")
```

**Note:** Tool calls are parsed but not automatically executed. The caller must handle tool execution based on the parsed tool_calls in the response.

## Features

### Reasoning Extraction
The adapter automatically extracts reasoning/thinking content from model output using:
- Tokenizer's native `parse_response()` method (for models that support it)
- Regex-based parsing for common reasoning tags: `<think>`, `<thinking>`, `<reasoning>`, `<chain_of_thought>`

Extracted thinking is available in `response.thinking` while the clean response is in `response.response`.

### Streaming Support
Real-time token generation using HuggingFace's `TextIteratorStreamer`:

```python
async for token in agent.stream(payload):
    print(token, end="", flush=True)
```

### Tool Call Parsing
Automatic detection and parsing of tool calls from model output:
- JSON format: `{"tool_calls": [...]}`
- Text format: `TOOL_CALL: func(arg=val)`

Parsed tool calls are available in `response.tool_calls`.

### Thread-Safe Loading
Uses `asyncio.Lock` and reference counting to ensure:
- No redundant model loads
- Safe concurrent access
- Automatic cleanup when references reach zero

## Limitations

1. **Limited Tool Execution** - Tool calls are parsed but not automatically executed
2. **Large Downloads** - Models can be 1-50GB+
3. **First Inference Slow** - Model loading takes time
4. **GPU Memory** - Large models need significant VRAM

## Troubleshooting

### Out of Memory
- Use a smaller model
- Enable quantization (`load_in_8bit=True` or `load_in_4bit=True`)
- Use CPU instead of GPU (`device="cpu"`)

### Slow Performance
- First inference is always slow (model loading)
- Use GPU if available (`device="cuda"`)
- Consider smaller models for faster inference

### Model Not Found
- Verify the model name on HuggingFace Hub
- Check internet connection for first download
- Some models require `trust_remote_code=True`
