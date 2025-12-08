"""Registry of all package documentation strings."""

# midori-ai-agent-base docs
AGENT_BASE_DOCS = """# midori-ai-agent-base Documentation

Common protocol (ABC) and data models for Midori AI agent backends.

## Overview

This package defines the `MidoriAiAgentProtocol` abstract base class that all agent backend implementations must follow. It also includes standardized data models for input payloads and responses.

## Usage

```python
from midori_ai_agent_base import MidoriAiAgentProtocol
from midori_ai_agent_base import AgentPayload
from midori_ai_agent_base import AgentResponse

# Create a custom agent by implementing the protocol
class MyAgent(MidoriAiAgentProtocol):
    async def invoke(self, payload: AgentPayload) -> AgentResponse:
        # Implementation here
        pass
    
    async def invoke_with_tools(self, payload: AgentPayload, tools: list) -> AgentResponse:
        # Implementation here
        pass
    
    async def get_context_window(self) -> int:
        return 128000
    
    async def supports_streaming(self) -> bool:
        return True
```

## Data Models

### AgentPayload

Standardized input for all agent backends:

- `user_message`: The user's message
- `thinking_blob`: Current thinking context (used when memory is not provided)
- `system_context`: System prompt/context
- `user_profile`: User profile data
- `tools_available`: List of available tool names
- `session_id`: Session identifier
- `metadata`: Optional additional metadata
- `reasoning_effort`: Optional reasoning effort configuration
- `memory`: Optional list of memory entries for conversation history

### MemoryEntryData

Lightweight representation of a memory entry for payload transport:

- `role`: Message role (user, assistant, system, tool)
- `content`: Text content of the message
- `timestamp`: Optional Unix timestamp
- `tool_calls`: Optional list of tool call dictionaries
- `metadata`: Optional additional metadata

### AgentResponse

Standardized output from all agent backends:

- `thinking`: Agent's reasoning/thinking
- `response`: The final response text
- `code`: Optional generated code
- `tool_calls`: Optional list of tool calls made
- `metadata`: Optional additional metadata

## Using Memory with Agents

The agent packages support passing conversation history via the `memory` field in `AgentPayload`. This integrates with the `midori-ai-agent-context-manager` package for persistence.

```python
from midori_ai_agent_base import AgentPayload, MemoryEntryData
from midori_ai_agent_context_manager import MemoryStore

# Create and populate a memory store
memory = MemoryStore(agent_id="my-agent")
memory.add_user_message("What's the weather?")
memory.add_assistant_message("Let me check...")
await memory.save("/path/to/memory.json")

# Convert memory entries to payload format
memory_data = [
    MemoryEntryData(role=e.role, content=e.content, timestamp=e.timestamp, tool_calls=[tc.model_dump() for tc in e.tool_calls] if e.tool_calls else None)
    for e in memory.entries
]

# Use memory in payload
payload = AgentPayload(
    user_message="What about tomorrow?",
    thinking_blob="",
    system_context="You are a weather assistant",
    user_profile={},
    tools_available=[],
    session_id="session-123",
    memory=memory_data,
)

response = await agent.invoke(payload)
```

## Protocol Methods

All implementations must provide these async methods:

- `invoke(payload)` - Process an agent payload and return a response
- `invoke_with_tools(payload, tools)` - Process with tool execution capability
- `get_context_window()` - Return the context window size
- `supports_streaming()` - Whether streaming responses are supported

## Factory Function

Use the `get_agent()` factory function to select backends by config:

```python
from midori_ai_agent_base import get_agent, AgentPayload

# Factory selects backend by config
agent = await get_agent(backend="langchain", model="carly-agi-pro", api_key=KEY, base_url=URL)

payload = AgentPayload(
    user_message="Hello",
    thinking_blob="",
    system_context="You are helpful",
    user_profile={},
    tools_available=[],
    session_id="session-123",
)

response = await agent.invoke(payload)
print(response.response)
```

## Configuration File

The package supports loading agent settings from a TOML configuration file. This allows you to persist settings like API keys, model names, and base URLs without hardcoding them.

### Config File Location

The package searches upward from its installation directory for a file named `config.toml`. Place the config file in your project root or any parent directory.

### Config File Format

```toml
# config.toml - Agent configuration example

[midori_ai_agent_base]
# Required settings
backend = "langchain"    # Options: "langchain", "openai"
model = "gpt-4"
api_key = "your-api-key"

# Optional settings
base_url = "https://api.openai.com/v1"

# Optional: Reasoning effort configuration
[midori_ai_agent_base.reasoning_effort]
effort = "medium"          # Options: "none", "minimal", "low", "medium", "high"
generate_summary = "auto"  # Options: "auto", "concise", "detailed"
summary = "auto"           # Options: "auto", "concise", "detailed"

# Backend-specific overrides (optional)
# These settings will override base settings when that backend is used
[midori_ai_agent_base.langchain]
model = "gpt-4-turbo"      # Override model for langchain backend

[midori_ai_agent_base.openai]
model = "gpt-4o"           # Override model for openai backend
```

### Using Config-Based Agent Creation

```python
from midori_ai_agent_base import get_agent_from_config, AgentPayload

# Load from config.toml in project directory
agent = await get_agent_from_config()

# Load from a specific config file
agent = await get_agent_from_config(config_path="my-config.toml")

# Override specific values from config
agent = await get_agent_from_config(model="gpt-4-turbo", api_key="override-key")

# Use backend-specific config overrides
agent = await get_agent_from_config(backend="openai")

# Use the agent as usual
payload = AgentPayload(
    user_message="Hello",
    thinking_blob="",
    system_context="You are helpful",
    user_profile={},
    tools_available=[],
    session_id="session-123",
)
response = await agent.invoke(payload)
```

### Config Precedence

Configuration values are resolved in the following order (highest to lowest priority):

1. Explicit arguments passed to `get_agent_from_config()`
2. Backend-specific overrides in `[midori_ai_agent_base.<backend>]`
3. Base settings in `[midori_ai_agent_base]`
4. None (will raise ValueError if required fields are missing)

### Loading Config Directly

You can also load the config without creating an agent:

```python
from midori_ai_agent_base import load_agent_config, AgentConfig

# Load base config
config: AgentConfig = load_agent_config()
print(config.backend, config.model, config.api_key)

# Load with backend-specific overrides merged in
config = load_agent_config(backend="openai")
print(config.model)  # Uses openai-specific model if defined

# Access reasoning effort settings
if config.reasoning_effort:
    print(config.reasoning_effort.effort)

# Access extra fields
print(config.extra)  # Dict of any additional key-value pairs
```
"""

# midori-ai-agent-context-manager docs
AGENT_CONTEXT_MANAGER_DOCS = """# Midori AI Agent Context Manager Documentation

## Overview

The `midori-ai-agent-context-manager` package provides context management for Midori AI agent backends. It enables agents to maintain conversation history in RAM and persist it to disk using Pydantic models for type-safe serialization.

## Core Concepts

### Memory Entries

Each conversation turn is stored as a `MemoryEntry` with:

- **role**: The message sender (user, assistant, system, or tool)
- **content**: The text content of the message
- **timestamp**: When the entry was created (Unix timestamp)
- **tool_calls**: Optional list of tool calls made during this turn
- **metadata**: Optional arbitrary metadata

### Memory Store

The `MemoryStore` class provides the main interface for memory management:

```python
from midori_ai_agent_context_manager import MemoryStore

memory = MemoryStore(agent_id="agent-1")
```

### Persistence

Memory is persisted as JSON using Pydantic's built-in serialization:

```python
# Save memory
await memory.save("/data/agents/agent-1.json")

# Load memory
loaded = await memory.load("/data/agents/agent-1.json")
```

## Usage Patterns

### Basic Conversation Tracking

```python
from midori_ai_agent_context_manager import MemoryStore

memory = MemoryStore(agent_id="my-agent")

# Track a conversation
memory.add_user_message("Hello!")
memory.add_assistant_message("Hi there! How can I help?")
memory.add_user_message("What's 2+2?")
memory.add_assistant_message("2+2 equals 4.")

# Get recent context
recent = memory.get_recent_entries(5)
```

### Tool Call Tracking

```python
from midori_ai_agent_context_manager import MemoryStore, ToolCallEntry

memory = MemoryStore(agent_id="tool-agent")

# User asks a question
memory.add_user_message("What's the weather in NYC?")

# Agent makes a tool call
tool_calls = [
    ToolCallEntry(
        name="get_weather",
        args={"location": "NYC"},
        result="Sunny, 72°F",
        call_id="call-123"
    )
]
memory.add_assistant_message("Let me check...", tool_calls=tool_calls)

# Tool result
memory.add_tool_result("get_weather", "Sunny, 72°F", call_id="call-123")

# Final response
memory.add_assistant_message("It's sunny and 72°F in NYC!")
```

### Memory Limits

Use `max_entries` to automatically trim old entries:

```python
# Keep only the last 50 entries
memory = MemoryStore(agent_id="limited-agent", max_entries=50)

# Old entries are automatically removed when limit is exceeded
for i in range(100):
    memory.add_user_message(f"Message {i}")

len(memory)  # Returns 50
```

### Summaries

Store conversation summaries for long-running sessions:

```python
memory = MemoryStore(agent_id="my-agent")

# After many messages, summarize older content
memory.summary = "User discussed weather and travel plans for NYC."

# Summary persists with save/load
await memory.save("/path/to/memory.json")
```

### Metadata

Attach metadata at entry or store level:

```python
# Entry-level metadata
memory.add_user_message(
    "Hello!",
    metadata={"source": "discord", "channel": "general"}
)

# Store-level metadata
memory.set_metadata("user_id", 12345)
memory.set_metadata("preferences", {"language": "en"})
```

## Integration with Agent Adapters

The context manager package is designed to integrate with the agent adapter packages:

### With LangchainAgent

```python
from midori_ai_agent_context_manager import MemoryStore
from midori_ai_agent_langchain import LangchainAgent
from midori_ai_agent_base import AgentPayload

# Create memory and agent
memory = MemoryStore(agent_id="langchain-agent")
agent = LangchainAgent(model="gpt-4", api_key="...", base_url="...")

# Build context from memory
recent = memory.get_recent_entries(10)
context = "\n".join([f"{e.role}: {e.content}" for e in recent])

# Invoke with memory context
payload = AgentPayload(
    user_message="What did we discuss?",
    thinking_blob=context,
    system_context="You are a helpful assistant.",
    user_profile={},
    tools_available=[],
    session_id="session-1"
)
response = await agent.invoke(payload)

# Store the response
memory.add_assistant_message(response.response)
await memory.save()
```

### With OpenAIAgentsAdapter

```python
from midori_ai_agent_context_manager import MemoryStore
from midori_ai_agent_openai import OpenAIAgentsAdapter

memory = MemoryStore(agent_id="openai-agent")
agent = OpenAIAgentsAdapter(model="gpt-4", api_key="...")

# Similar pattern - use memory.entries for context building
```

## File Format

Memory is stored as JSON with the following structure:

```json
{
  "agent_id": "my-agent",
  "entries": [
    {
      "role": "user",
      "content": "Hello!",
      "timestamp": 1701234567.89,
      "tool_calls": null,
      "metadata": null
    },
    {
      "role": "assistant",
      "content": "Hi there!",
      "timestamp": 1701234568.12,
      "tool_calls": null,
      "metadata": null
    }
  ],
  "summary": null,
  "created_at": 1701234567.0,
  "updated_at": 1701234568.12,
  "metadata": null,
  "version": "1.0.0"
}
```

## Best Practices

1. **Use meaningful agent IDs**: The agent_id helps identify memory files and debug issues.

2. **Save explicitly**: Memory is not auto-saved. Call `await memory.save()` after important operations.

3. **Handle load failures**: `load()` returns `False` if the file doesn't exist. Initialize with defaults in that case.

4. **Use summaries for long conversations**: Summarize older content to maintain context without unlimited growth.

5. **Set appropriate limits**: Use `max_entries` to prevent unbounded memory growth.

6. **Include tool calls**: Track tool usage for better context and debugging.

7. **Use auto-compression for long sessions**: Configure a `MemoryCompressor` to automatically summarize when approaching context limits.

## Auto-Compression

### Overview

The auto-compression feature allows automatic summarization of conversation history when approaching context window limits. This is essential for long-running conversations where the token count would otherwise exceed the model's context window.

### Configuration

```python
from midori_ai_agent_context_manager import CompressionConfig, MemoryCompressor

# Using a known model name (context window looked up automatically)
config = CompressionConfig(
    model_name="gpt-oss-120b",      # Known model with 131k context
    compression_threshold=0.8       # Compress at 80% (default)
)

# Or specify context window explicitly (in thousands of tokens)
config = CompressionConfig(
    context_window=131,             # 131k tokens
    compression_threshold=0.8       # Compress at 80%
)
```

### Known Models

The package includes preset context windows for known gpt-oss models (in thousands of tokens):

| Model | Context Window (k) |
|-------|-------------------|
| gpt-oss-120b, gpt-oss-20b | 131 |

### Creating a Compressor

The compressor requires a summarizer callable - an async function that takes text and returns a summary. This allows you to use your own LLM/agent for summarization:

```python
from midori_ai_agent_context_manager import MemoryCompressor, CompressionConfig

# Define your summarizer
async def my_summarizer(text: str) -> str:
    # Use your LLM to generate a summary
    response = await llm.invoke(text)
    return response

config = CompressionConfig(model_name="gpt-oss-120b")
compressor = MemoryCompressor(config=config, summarizer=my_summarizer)
```

### Compression Output Format

When compression occurs, the memory is reduced to:

1. **System message**: Preserves the original system context
2. **User message**: "What do you remember about our chat?" (configurable)
3. **Assistant message**: The generated summary

This format ensures the compressed memory maintains proper conversation structure.

### Usage Examples

#### Check and Compress

```python
from midori_ai_agent_context_manager import MemoryStore, MemoryCompressor, CompressionConfig

memory = MemoryStore(agent_id="my-agent")
# ... add many messages ...

config = CompressionConfig(model_name="gpt-oss-120b", compression_threshold=0.8)
compressor = MemoryCompressor(config=config, summarizer=my_summarizer)

# Check if compression is needed
if compressor.should_compress(memory.entries):
    compressed = await compressor.compress(
        entries=memory.entries,
        system_context="You are a helpful assistant."
    )
    # Replace memory with compressed version
    memory.clear()
    for entry in compressed:
        memory.add_entry(entry)
```

#### Auto-Compress If Needed

```python
# Automatic check and compress in one call
entries, was_compressed = await compressor.compress_if_needed(
    entries=memory.entries,
    system_context="You are a helpful assistant."
)

if was_compressed:
    memory.clear()
    for entry in entries:
        memory.add_entry(entry)
```

#### Custom Summary Prompt

```python
config = CompressionConfig(
    model_name="gpt-oss-120b",
    summary_prompt="Please tell me what we discussed."  # Custom prompt
)
```

### Integration with Agent Adapters

```python
from midori_ai_agent_context_manager import MemoryStore, MemoryCompressor, CompressionConfig
from midori_ai_agent_openai import OpenAIAgentsAdapter
from midori_ai_agent_base import AgentPayload

# Create adapter and memory
adapter = OpenAIAgentsAdapter(model="gpt-4", api_key="...")
memory = MemoryStore(agent_id="my-agent")

# Create compressor that uses the same adapter for summarization
async def summarizer(text: str) -> str:
    payload = AgentPayload(
        user_message=text,
        thinking_blob="",
        system_context="Summarize the following conversation concisely.",
        user_profile={},
        tools_available=[],
        session_id="summary"
    )
    response = await adapter.invoke(payload)
    return response.response

config = CompressionConfig(model_name="gpt-oss-120b")
compressor = MemoryCompressor(config=config, summarizer=summarizer)
```
"""

# midori-ai-agent-huggingface docs
AGENT_HUGGINGFACE_DOCS = """# midori-ai-agent-huggingface Documentation

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
    \"\"\"Search for information.\"\"\"
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
"""

# midori-ai-agent-langchain docs
AGENT_LANGCHAIN_DOCS = """# midori-ai-agent-langchain Documentation

Langchain implementation of the Midori AI agent protocol.

## Overview

This package provides a Langchain-based agent implementation that adheres to the `MidoriAiAgentProtocol` interface. It uses `langchain-openai` for model invocation with full async support.

## Usage

```python
from midori_ai_agent_langchain import LangchainAgent
from midori_ai_agent_base import AgentPayload

# Create a Langchain agent
agent = LangchainAgent(
    model="carly-agi-pro",
    api_key="your-api-key",
    base_url="https://api.example.com/v1",
)

# Invoke the agent
payload = AgentPayload(
    user_message="Hello, how are you?",
    thinking_blob="",
    system_context="You are a helpful assistant",
    user_profile={"name": "User"},
    tools_available=[],
    session_id="session-123",
)

response = await agent.invoke(payload)
print(response.response)
```

## Configuration

The `LangchainAgent` accepts the following parameters:

- `model`: Model name to use (e.g., "carly-agi-pro")
- `api_key`: API key for authentication
- `base_url`: Base URL for the API endpoint
- `temperature`: Sampling temperature (default: 0.2)
- `context_window`: Context window size (default: 128000)
- `**kwargs`: Additional arguments passed to ChatOpenAI

## Features

- 100% async - uses `ainvoke()` for all model calls
- Tool binding support via `invoke_with_tools()`
- Automatic message formatting for Langchain
- Integrated logging via `midori_ai_logger`
"""

# midori-ai-agent-openai docs
AGENT_OPENAI_DOCS = """# midori-ai-agent-openai Documentation

OpenAI Agents SDK implementation of the Midori AI agent protocol.

## Overview

This package provides an OpenAI Agents SDK implementation that adheres to the `MidoriAiAgentProtocol` interface. It uses the `openai-agents` library with `Agent` and `Runner` for full async agent support.

## Usage

```python
from midori_ai_agent_openai import OpenAIAgentsAdapter
from midori_ai_agent_base import AgentPayload

# Create an OpenAI Agents adapter
agent = OpenAIAgentsAdapter(
    model="gpt-4",
    api_key="your-api-key",
)

# Invoke the agent
payload = AgentPayload(
    user_message="Hello, how are you?",
    thinking_blob="",
    system_context="You are a helpful assistant",
    user_profile={"name": "User"},
    tools_available=[],
    session_id="session-123",
)

response = await agent.invoke(payload)
print(response.response)
```

## Configuration

The `OpenAIAgentsAdapter` accepts the following parameters:

- `model`: Model name to use (e.g., "gpt-4", "carly-agi-pro")
- `api_key`: API key for authentication
- `base_url`: Base URL for the API endpoint (optional)
- `context_window`: Context window size (default: 128000)

## Features

- Uses `openai-agents` library with `Agent` and `Runner`
- 100% async using `Runner.run_async()`
- Tool binding support via `invoke_with_tools()`
- Integrated logging via `midori_ai_logger`

## Reference

See the Swarm-o-codex project for advanced agent patterns:
https://github.com/Midori-AI-OSS/Midori-AI/tree/main/Experimentation/Swarm-o-codex
"""

# midori-ai-compactor docs
COMPACTOR_DOCS = """# midori-ai-compactor Documentation

Flexible consolidation of multi-model reasoning outputs using agents.

## Overview

When using multiple reasoning models (any number, any language), their outputs need to be combined into a single coherent message. This package provides a **flexible consolidation system** that:

- Accepts a **list of strings** from any number of reasoning models (not limited to a fixed number)
- Supports **any language** the user wants to use for reasoning
- Uses an **agent** from `midori-ai-agent-base` protocol to intelligently merge outputs
- Returns a **single, easy-to-parse message string**

## Key Features

- **Agent-powered**: Leverages `MidoriAiAgentProtocol` for intelligent merging
- **Language-agnostic**: Supports outputs in any language
- **Flexible input**: Accepts `list[str]` of any length
- **Simple output**: Returns one consolidated `str`
- **Configurable prompts**: Customizable consolidation prompts
- **100% async-friendly**: Fully asynchronous implementation

## Usage

### Basic Usage

```python
from midori_ai_compactor import ThinkingCompactor
from midori_ai_agent_base import get_agent

# Create the agent for consolidation
agent = await get_agent(
    backend="langchain",
    model="your-model",
    api_key="your-key",
)

# Create compactor with agent
compactor = ThinkingCompactor(agent=agent)

# Usage - any number of reasoning model outputs
model_outputs: list[str] = [
    preprocessing_result_1,
    preprocessing_result_2,
    working_awareness_1,
    # ... any number of additional outputs in any language
]

# Consolidate into single message
consolidated = await compactor.compact(model_outputs)
# Returns a single, easy-to-parse string
```

### Custom Consolidation Prompt

```python
from midori_ai_compactor import ThinkingCompactor, CompactorConfig

# Create config with custom prompt
config = CompactorConfig(
    custom_prompt="Merge the following outputs into a summary:\n\n{outputs}"
)

# Create compactor with custom config
compactor = ThinkingCompactor(agent=agent, config=config)
```

### Using Config File

The compactor supports loading configuration from a TOML file:

```toml
# config.toml
[midori_ai_compactor]
custom_prompt = "Merge the following outputs:\n\n{outputs}"
```

```python
from midori_ai_compactor import ThinkingCompactor, load_compactor_config

# Load config from file
config = load_compactor_config()
compactor = ThinkingCompactor(agent=agent, config=config)
```

## Example Input/Output

**Input** (list of model outputs):
```python
outputs = [
    "## Analysis\n- User asking about Python async...",
    "## 분석\n- 사용자가 비동기 프로그래밍에 대해 묻고 있음...",  # Korean
    "## Observations\n- Technical question detected",
]
```

**Output** (single consolidated string):
```
## Consolidated Analysis

### User Intent
- Learning async/await patterns in Python

### Key Observations
- Technical question from experienced developer

### Confidence: High
```

## API Reference

### ThinkingCompactor

The main class for consolidating multiple model outputs.

#### Constructor

```python
ThinkingCompactor(agent: MidoriAiAgentProtocol, config: Optional[CompactorConfig] = None)
```

- `agent`: An instance of `MidoriAiAgentProtocol` to use for consolidation
- `config`: Optional configuration object for customizing consolidation behavior

#### Methods

##### `compact(outputs: list[str]) -> str`

Consolidate multiple model outputs into a single message.

- `outputs`: List of strings from reasoning models
- Returns: A single consolidated string

### CompactorConfig

Configuration dataclass for the compactor.

```python
@dataclass
class CompactorConfig:
    custom_prompt: Optional[str] = None
```

- `custom_prompt`: Optional custom prompt template. Use `{outputs}` placeholder for the formatted outputs.

### load_compactor_config()

Load configuration from a TOML file.

```python
def load_compactor_config() -> CompactorConfig
```

Returns a `CompactorConfig` with values loaded from `config.toml`.

## Dependencies

- `midori-ai-agent-base` - For agent protocol
- `midori_ai_logger` - For logging
"""

# midori-ai-context-bridge docs
CONTEXT_BRIDGE_DOCS = """# midori-ai-context-bridge Documentation

Persistent thinking cache with time-based memory decay for AI reasoning models. Uses `midori-ai-vector-manager` for vector storage.

## Overview

The Context Bridge package solves the problem of reasoning models "rehashing" the same prompts by providing a caching layer that:

- Uses `midori-ai-vector-manager` for vector storage (backed by ChromaDB)
- Implements gradual memory corruption for older data to simulate natural forgetting
- Supports different decay rates for different model types
- Automatically cleans up data older than the removal threshold

## Architecture

Context Bridge now depends on `midori-ai-vector-manager` for all vector storage operations:
- **Storage**: Delegates to `ChromaVectorStore` from vector-manager
- **Decay/Corruption**: Retained in context-bridge as domain-specific logic
- **ReasoningEntry**: Wraps `VectorEntry` objects with reasoning-specific fields

## Installation

See README.md for installation instructions.

## Core Concepts

### Model Types

The package supports two model types with different decay characteristics:

| Model Type | Corruption Start | Full Removal |
|------------|------------------|--------------|
| PREPROCESSING | 30 minutes | 90 minutes |
| WORKING_AWARENESS | 12 hours | 36 hours |

- **PREPROCESSING**: Fast-decaying tactical memory for preprocessing analysis
- **WORKING_AWARENESS**: Slow-decaying strategic memory for deeper context

### Memory Decay

Memory corruption simulates natural forgetting:

1. **Fresh data** (age < decay threshold): No corruption
2. **Aging data** (between decay and removal threshold): Progressive character-level corruption
3. **Old data** (age >= removal threshold): Automatically removed

## Usage

### Basic Usage

```python
from midori_ai_context_bridge import ContextBridge, ModelType

# Initialize with default settings
bridge = ContextBridge(max_tokens_per_summary=500)

# Store reasoning after model inference
await bridge.store_reasoning(
    session_id="username:discordid",
    text="The user asked about weather. Key entities: weather, location...",
    model_type=ModelType.PREPROCESSING
)

# Get prior reasoning before next model inference
context = await bridge.get_prior_reasoning(
    session_id="username:discordid",
    model_type=ModelType.PREPROCESSING
)
# Returns compressed context with corruption applied based on age
```

### Integration with Reasoning Models

```python
from midori_ai_context_bridge import ContextBridge, ModelType

bridge = ContextBridge(max_tokens_per_summary=500)

async def get_thinking(past_messages, username, discordid, ...):
    session_id = f"{username}:{discordid}"
    
    # Get prior reasoning for preprocessing (30 min decay)
    preprocessing_context = await bridge.get_prior_reasoning(
        session_id,
        model_type=ModelType.PREPROCESSING
    )
    
    # Get prior reasoning for working awareness (12 hour decay)
    working_context = await bridge.get_prior_reasoning(
        session_id,
        model_type=ModelType.WORKING_AWARENESS
    )
    
    # ... run preprocessing models with preprocessing_context ...
    # ... run working awareness models with working_context ...
    
    # Store results for next time
    await bridge.store_reasoning(
        session_id,
        preprocessing_result,
        model_type=ModelType.PREPROCESSING
    )
    await bridge.store_reasoning(
        session_id,
        working_result,
        model_type=ModelType.WORKING_AWARENESS
    )
    
    return thinking_text
```

### Custom Decay Configuration

```python
from midori_ai_context_bridge import (
    ContextBridge,
    BridgeConfig,
    DecayConfig,
    ModelType,
)

# Custom decay: preprocessing expires faster
custom_config = BridgeConfig(
    max_tokens_per_summary=1000,
    preprocessing_decay=DecayConfig(
        decay_minutes=15,        # Start corrupting after 15 minutes
        removal_multiplier=3.0,  # Remove after 45 minutes
        corruption_intensity=0.4 # Higher corruption rate
    ),
    working_awareness_decay=DecayConfig(
        decay_minutes=360,       # Start corrupting after 6 hours
        removal_multiplier=3.0,  # Remove after 18 hours
        corruption_intensity=0.2 # Lower corruption rate
    ),
)

bridge = ContextBridge(config=custom_config)
```

### Persistent Storage

```python
# Use default persistent storage (~/.midoriai/vectorstore/chromadb/)
bridge = ContextBridge(max_tokens_per_summary=500)

# Use custom persistent storage path
bridge = ContextBridge(
    max_tokens_per_summary=500,
    persist_directory="/path/to/chromadb"
)

# Use ephemeral in-memory storage (not persisted)
bridge = ContextBridge(
    max_tokens_per_summary=500,
    persist_directory=None
)
```

### Session Management

```python
# Get statistics for a session
stats = await bridge.get_session_stats("username:discordid")
print(stats)
# {
#     "session_id": "username:discordid",
#     "preprocessing_count": 5,
#     "working_awareness_count": 3,
#     "total_count": 8,
#     "oldest_preprocessing_age_minutes": 25.5,
#     "oldest_working_age_minutes": 120.3
# }

# Clear all entries for a session
removed = await bridge.clear_session("username:discordid")
print(f"Removed {removed} entries")

# Manual cleanup of expired entries
removed = await bridge.cleanup_expired()
print(f"Cleaned up {removed} expired entries")
```

## API Reference

### ContextBridge

Main interface for the context bridge.

#### Constructor

```python
ContextBridge(
    max_tokens_per_summary: int = 500,
    config: Optional[BridgeConfig] = None,
    persist_directory: Optional[str] = None
)
```

#### Methods

- `store_reasoning(session_id, text, model_type, metadata=None)` - Store reasoning text
- `get_prior_reasoning(session_id, model_type, include_corrupted=True)` - Get prior reasoning with decay
- `cleanup_expired()` - Remove all expired entries
- `get_session_stats(session_id)` - Get session statistics
- `clear_session(session_id)` - Clear all entries for a session
- `count()` - Get total entry count

### ModelType

Enum for model types:
- `ModelType.PREPROCESSING` - 30 minute decay
- `ModelType.WORKING_AWARENESS` - 12 hour decay

### BridgeConfig

Configuration dataclass:
- `max_tokens_per_summary: int` - Max tokens for compressed output
- `chroma_collection_name: str` - ChromaDB collection name
- `preprocessing_decay: DecayConfig` - Decay config for preprocessing
- `working_awareness_decay: DecayConfig` - Decay config for working awareness

### DecayConfig

Decay configuration dataclass:
- `decay_minutes: int` - Minutes before corruption begins
- `removal_multiplier: float` - Multiplier for removal threshold (default 3.0)
- `corruption_intensity: float` - Max corruption rate (0.0 to 1.0)

### MemoryCorruptor

Low-level corruption logic:
- `calculate_severity(age_minutes)` - Get corruption severity (0.0 to 1.0)
- `corrupt_text(text, age_minutes)` - Apply corruption to text
- `should_remove(age_minutes)` - Check if data should be removed
- `process_text(text, age_minutes)` - Process with corruption and removal

### ChromaStorage

Direct access to ChromaDB storage:
- `store(session_id, text, model_type, metadata=None)` - Store entry
- `get_entries_for_session(session_id, model_type=None, limit=100)` - Get entries
- `delete_entries(entry_ids)` - Delete by IDs
- `get_all_entries(limit=1000)` - Get all entries
- `count()` - Get total count
- `clear()` - Clear all entries

### ContextCompressor

Context compression utilities:
- `compress(texts, separator)` - Compress multiple texts
- `compress_with_labels(labeled_texts, separator)` - Compress with labels
- `estimate_tokens(text)` - Estimate token count

## Memory Corruption Details

The corruption algorithm:

1. Calculate severity based on age: `severity = (age - decay_threshold) / (removal_threshold - decay_threshold)`
2. For each character, with probability `severity * corruption_intensity`:
   - 50% chance: remove the character
   - 50% chance: replace with random lowercase letter or space
3. Severity increases linearly from 0% at decay threshold to 100% at removal threshold

Example corruption progression:
- Fresh (0-30 min): "The user asked about weather in Seattle"
- Aging (45 min): "The user asked abut weather in eatle"
- Old (75 min): "Th  us r asked but wath r n stle"
- Expired (90+ min): Entry removed

## Dependencies

- `midori_ai_vector_manager` - Vector storage abstraction (backed by ChromaDB)
- `midori_ai_logger` - Logging (via git+)
- `pydantic>=2.0.0` - Data validation and models
"""

# midori-ai-media-lifecycle docs
MEDIA_LIFECYCLE_DOCS = """# midori-ai-media-lifecycle Documentation

Time-based lifecycle management for media objects with parsing probability decay and automatic cleanup.

## Overview

This package provides lifecycle management capabilities for media objects, featuring:

- **Time-based parsing probability decay**: Media becomes less likely to be parsed as it ages
- **Configurable decay timeline**: Customize full-probability and zero-probability thresholds via `DecayConfig`
- **Automatic cleanup**: Background scheduler removes aged-out media
- **Lifecycle tracking**: Mark media as loaded/parsed with timestamps
- **100% async-friendly implementation**

**Note:** All lifecycle configuration is managed through `DecayConfig` at the manager level. Individual media objects do not have per-media ageout settings - this ensures consistent lifecycle management across all stored media.

## Quick Start

```python
from pathlib import Path

from midori_ai_media_lifecycle import DecayConfig
from midori_ai_media_lifecycle import LifecycleManager
from midori_ai_media_lifecycle import create_lifecycle_manager

from midori_ai_media_vault import MediaCrypto
from midori_ai_media_vault import MediaMetadata
from midori_ai_media_vault import MediaObject
from midori_ai_media_vault import MediaStorage
from midori_ai_media_vault import MediaType


async def example():
    # Create lifecycle manager with default decay (35 min full, 90 min zero)
    manager = create_lifecycle_manager(base_path=Path("./media_storage"))

    # Or with custom decay config
    config = DecayConfig(full_probability_minutes=30.0, zero_probability_minutes=60.0)
    manager = create_lifecycle_manager(base_path=Path("./media_storage"), config=config)

    # Create and save media object
    content = b"photo bytes here..."
    encrypted, key, hash_str = MediaCrypto.encrypt(content)
    media = MediaObject(
        id="photo-001",
        media_type=MediaType.PHOTO,
        metadata=MediaMetadata(content_hash=hash_str),
        user_id="user-123",
        encrypted_content=encrypted,
        encryption_key=key,
        content_integrity_hash=hash_str,
    )
    await manager.storage.save(media)

    # Check parsing probability
    probability = manager.get_parsing_probability(media)
    print(f"Parsing probability: {probability:.1%}")

    # Probabilistically decide to parse
    if manager.should_parse(media):
        # Process the media...
        await manager.mark_parsed(media)

    # Check if aged out
    if manager.is_aged_out(media):
        print("Media has aged out")
```

## Decay Timeline

The default decay configuration applies to **all media objects** in the system:

| Age | Parsing Probability |
|-----|---------------------|
| 0-35 min | 100% |
| 35 min | 100% (decay starts) |
| 62.5 min | 50% |
| 90 min | 0% (aged out) |
| 90+ min | Should be cleaned up |

**Important:** The decay timeline is set at the `LifecycleManager` level via `DecayConfig` and applies uniformly to all media. There are no per-media ageout overrides.

### Custom Configuration

```python
from midori_ai_media_lifecycle import DecayConfig

# Shorter decay window
config = DecayConfig(full_probability_minutes=15.0, zero_probability_minutes=45.0)

# Longer decay window
config = DecayConfig(full_probability_minutes=60.0, zero_probability_minutes=180.0)
```

## Decay Functions

### get_parsing_probability

Calculate parsing probability based on media age:

```python
from datetime import datetime
from datetime import timezone

from midori_ai_media_lifecycle import DecayConfig
from midori_ai_media_lifecycle import get_parsing_probability

time_saved = datetime.now(timezone.utc)
probability = get_parsing_probability(time_saved)  # Returns 1.0 for fresh media

# With custom config
config = DecayConfig(full_probability_minutes=30.0, zero_probability_minutes=60.0)
probability = get_parsing_probability(time_saved, config)
```

### should_parse

Make a probabilistic decision about whether to parse:

```python
from midori_ai_media_lifecycle import should_parse

if should_parse(time_saved):
    # Parse the media
    pass
```

### is_aged_out

Check if media has passed the ageout threshold:

```python
from midori_ai_media_lifecycle import is_aged_out

if is_aged_out(time_saved):
    # Media should be cleaned up
    pass
```

### get_age_minutes

Get the age of media in minutes:

```python
from midori_ai_media_lifecycle import get_age_minutes

age = get_age_minutes(time_saved)
print(f"Media is {age:.1f} minutes old")
```

## Lifecycle Manager

The `LifecycleManager` class provides high-level operations for media lifecycle:

```python
from pathlib import Path

from midori_ai_media_lifecycle import DecayConfig
from midori_ai_media_lifecycle import LifecycleManager
from midori_ai_media_lifecycle import create_lifecycle_manager

from midori_ai_media_vault import MediaStorage


# Using factory function
manager = create_lifecycle_manager(base_path=Path("./media"))

# Or with existing storage
storage = MediaStorage(base_path=Path("./media"))
config = DecayConfig()
manager = LifecycleManager(storage=storage, config=config)
```

### Methods

#### get_parsing_probability(media)

Get probability for a MediaObject:

```python
probability = manager.get_parsing_probability(media)
```

#### should_parse(media)

Probabilistic parse decision:

```python
if manager.should_parse(media):
    # Process media
    pass
```

#### is_aged_out(media)

Check if media is aged out:

```python
if manager.is_aged_out(media):
    print("Media has aged out")
```

#### mark_loaded(media)

Update time_loaded and persist:

```python
media = await manager.mark_loaded(media)
print(f"Loaded at: {media.metadata.time_loaded}")
```

#### mark_parsed(media)

Update time_parsed and persist:

```python
media = await manager.mark_parsed(media)
print(f"Parsed at: {media.metadata.time_parsed}")
```

#### cleanup_aged_media()

Remove all aged-out media from storage:

```python
deleted_ids = await manager.cleanup_aged_media()
print(f"Cleaned up {len(deleted_ids)} media objects")
```

#### get_media_status(media_id)

Get comprehensive status for a media object:

```python
status = await manager.get_media_status("photo-001")
print(f"Probability: {status['probability']:.1%}")
print(f"Aged out: {status['aged_out']}")
print(f"Time saved: {status['time_saved']}")
```

## Cleanup Scheduler

The `CleanupScheduler` runs periodic background cleanup:

```python
from midori_ai_media_lifecycle import CleanupScheduler
from midori_ai_media_lifecycle import create_lifecycle_manager


# Create manager and scheduler
manager = create_lifecycle_manager(base_path=Path("./media"))
scheduler = CleanupScheduler(
    lifecycle_manager=manager,
    interval_seconds=300.0,  # Run every 5 minutes
)

# Start background cleanup
scheduler.start()

# Check if running
print(f"Running: {scheduler.is_running}")

# Stop when done
await scheduler.stop()
```

### Cleanup Callback

Register a callback to be notified of cleanups:

```python
def on_cleanup(deleted_ids: list[str]) -> None:
    print(f"Deleted {len(deleted_ids)} media objects")
    for media_id in deleted_ids:
        print(f"  - {media_id}")


scheduler = CleanupScheduler(lifecycle_manager=manager, interval_seconds=60.0, on_cleanup=on_cleanup)
scheduler.start()
```

### Manual Cleanup

Run cleanup once without scheduling:

```python
deleted_ids = await scheduler.run_once()
```

## Integration with Media Vault

This package builds on `midori-ai-media-vault`:

```python
from pathlib import Path

from midori_ai_media_lifecycle import CleanupScheduler
from midori_ai_media_lifecycle import DecayConfig
from midori_ai_media_lifecycle import LifecycleManager

from midori_ai_media_vault import MediaCrypto
from midori_ai_media_vault import MediaMetadata
from midori_ai_media_vault import MediaObject
from midori_ai_media_vault import MediaStorage
from midori_ai_media_vault import MediaType


async def full_workflow():
    # Setup
    storage = MediaStorage(base_path=Path("./media"))
    config = DecayConfig(full_probability_minutes=35.0, zero_probability_minutes=90.0)
    manager = LifecycleManager(storage=storage, config=config)

    # Create media
    content = b"image data..."
    encrypted, key, hash_str = MediaCrypto.encrypt(content)
    media = MediaObject(
        id="img-001",
        media_type=MediaType.PHOTO,
        metadata=MediaMetadata(content_hash=hash_str),
        user_id="user-123",
        encrypted_content=encrypted,
        encryption_key=key,
        content_integrity_hash=hash_str,
    )
    await storage.save(media)

    # Load and process
    loaded = await storage.load("img-001")
    loaded = await manager.mark_loaded(loaded)

    if manager.should_parse(loaded):
        # Decrypt and parse content
        decrypted = MediaCrypto.decrypt(loaded.encrypted_content, loaded.encryption_key, loaded.content_integrity_hash)
        # ... process decrypted content ...
        await manager.mark_parsed(loaded)

    # Start background cleanup
    scheduler = CleanupScheduler(lifecycle_manager=manager, interval_seconds=300.0)
    scheduler.start()

    # ... application runs ...

    # Cleanup on shutdown
    await scheduler.stop()
```

## Best Practices

1. **Use appropriate decay times**: Choose decay windows that match your data retention requirements.

2. **Monitor cleanup operations**: Use the callback parameter to track what gets cleaned up.

3. **Start scheduler early**: Start the cleanup scheduler when your application initializes.

4. **Graceful shutdown**: Always stop the scheduler before application exit.

5. **Check probability before expensive operations**: Use `should_parse()` to avoid processing stale data.

## Error Handling

```python
from midori_ai_media_lifecycle import create_lifecycle_manager


manager = create_lifecycle_manager(base_path=Path("./media"))

try:
    status = await manager.get_media_status("unknown-id")
except FileNotFoundError:
    print("Media not found")
```

## Integration with Other Packages

This package is part of the media storage family:

- **midori-ai-media-vault**: Encrypted storage foundation (required dependency)
- **midori-ai-media-request**: Type-safe request/response interface (future)
"""

# midori-ai-media-request docs
MEDIA_REQUEST_DOCS = """# midori-ai-media-request Documentation

Type-safe request/response protocol for media parsing in agent systems.

## Overview

This package provides a standardized way for agents to request media with:

- **Type validation**: Ensures requested type matches stored media type
- **Priority-based queuing**: Support for LOW, NORMAL, HIGH, CRITICAL priorities
- **Decay-aware responses**: Respects parsing probability from media lifecycle
- **Clear status tracking**: PENDING, APPROVED, DENIED, PROCESSING, COMPLETED, EXPIRED
- **100% async-friendly implementation**

## Quick Start

```python
from pathlib import Path

from midori_ai_media_lifecycle import create_lifecycle_manager

from midori_ai_media_request import MediaRequest
from midori_ai_media_request import MediaRequestHandler
from midori_ai_media_request import RequestPriority

from midori_ai_media_vault import MediaType


async def example():
    # Create lifecycle manager (handles storage and decay)
    manager = create_lifecycle_manager(base_path=Path("./media_storage"))

    # Create request handler
    handler = MediaRequestHandler(lifecycle_manager=manager)

    # Create a request for media
    request = MediaRequest(
        media_id="photo-001",
        requested_type=MediaType.PHOTO,
        requester_id="agent-123",
        priority=RequestPriority.HIGH,
        reason="User requested photo analysis",
    )

    # Process the request
    response = await handler.request_media(request)

    if response.status == RequestStatus.COMPLETED:
        # Access decrypted content
        content = response.decrypted_content
        print(f"Got {len(content)} bytes of content")
    else:
        # Handle denial or expiration
        print(f"Request {response.status.value}: {response.denial_reason}")
```

## Request/Response Flow

The media request flow follows these steps:

1. **Agent creates MediaRequest** with `media_id`, `requested_type`, `requester_id`
2. **Handler loads media** from storage
3. **Type validation**: If `requested_type != media.media_type`, return DENIED
4. **Decay check**: If `is_aged_out()`, return EXPIRED
5. **Probability check**: If `should_parse()` returns False, return DENIED with probability
6. **Success**: Decrypt content, update parsed timestamp, return COMPLETED with content

## Data Models

### RequestPriority

Enum for request priority levels:

```python
from midori_ai_media_request import RequestPriority

RequestPriority.LOW       # "low"
RequestPriority.NORMAL    # "normal" (default)
RequestPriority.HIGH      # "high"
RequestPriority.CRITICAL  # "critical"
```

### RequestStatus

Enum for request status:

```python
from midori_ai_media_request import RequestStatus

RequestStatus.PENDING     # "pending" - Request received, not yet processed
RequestStatus.APPROVED    # "approved" - Request approved, awaiting processing
RequestStatus.DENIED      # "denied" - Request denied (type mismatch, probability)
RequestStatus.PROCESSING  # "processing" - Request being processed
RequestStatus.COMPLETED   # "completed" - Request fulfilled, content available
RequestStatus.EXPIRED     # "expired" - Media has aged out
```

### MediaRequest

Request model for media parsing:

```python
from midori_ai_media_request import MediaRequest
from midori_ai_media_request import RequestPriority

from midori_ai_media_vault import MediaType

request = MediaRequest(
    media_id="photo-001",           # Required: ID of media to request
    requested_type=MediaType.PHOTO, # Required: Expected media type
    requester_id="agent-123",       # Required: ID of requesting agent
    priority=RequestPriority.HIGH,  # Optional: Priority level (default: NORMAL)
    reason="Analysis needed",       # Optional: Reason for request
)

# Auto-populated fields:
# - request_time: datetime (current UTC time)
```

### MediaResponse

Response model for media requests:

```python
from midori_ai_media_request import MediaResponse
from midori_ai_media_request import RequestStatus

from midori_ai_media_vault import MediaType

# Successful response
response = MediaResponse(
    request_id="req-uuid-001",          # Unique request identifier
    media_id="photo-001",               # Requested media ID
    status=RequestStatus.COMPLETED,     # Request status
    decrypted_content=b"image bytes",   # Decrypted content (COMPLETED only)
    media_type=MediaType.PHOTO,         # Actual media type
    parsing_probability=1.0,            # Current parsing probability
)

# Denied response
response = MediaResponse(
    request_id="req-uuid-002",
    media_id="photo-002",
    status=RequestStatus.DENIED,
    denial_reason="Type mismatch: requested video, found photo",
    media_type=MediaType.PHOTO,
    parsing_probability=0.8,
)

# Expired response
response = MediaResponse(
    request_id="req-uuid-003",
    media_id="photo-003",
    status=RequestStatus.EXPIRED,
    denial_reason="Media has aged out",
    parsing_probability=0.0,
)
```

## Request Handler

### MediaRequestHandler

The default implementation of media request handling:

```python
from pathlib import Path

from midori_ai_media_lifecycle import create_lifecycle_manager

from midori_ai_media_request import MediaRequestHandler


# Create handler with lifecycle manager
manager = create_lifecycle_manager(base_path=Path("./media"))
handler = MediaRequestHandler(lifecycle_manager=manager)
```

### Methods

#### request_media(request)

Process a media request:

```python
from midori_ai_media_request import MediaRequest
from midori_ai_media_request import RequestStatus

from midori_ai_media_vault import MediaType


request = MediaRequest(
    media_id="photo-001",
    requested_type=MediaType.PHOTO,
    requester_id="agent-123",
)
response = await handler.request_media(request)

if response.status == RequestStatus.COMPLETED:
    content = response.decrypted_content
    # Process content...
elif response.status == RequestStatus.DENIED:
    print(f"Denied: {response.denial_reason}")
elif response.status == RequestStatus.EXPIRED:
    print(f"Expired: {response.denial_reason}")
```

#### get_request_status(request_id)

Get status of a previous request:

```python
try:
    response = await handler.get_request_status("req-uuid-001")
    print(f"Status: {response.status.value}")
except KeyError:
    print("Request not found")
```

#### cancel_request(request_id)

Cancel a pending request:

```python
cancelled = await handler.cancel_request("req-uuid-001")
if cancelled:
    print("Request cancelled")
else:
    print("Request not found or already processed")
```

#### list_ids_by_type(media_type, requester_id)

List all media IDs of a specific type for batch operations:

```python
from midori_ai_media_vault import MediaType


# Get all photo IDs
photo_ids = await handler.list_ids_by_type(MediaType.PHOTO, requester_id="agent-123")

# Get all audio IDs for transcription batch
audio_ids = await handler.list_ids_by_type(MediaType.AUDIO, requester_id="agent-123")

# Loop over and process each
for photo_id in photo_ids:
    request = MediaRequest(
        media_id=photo_id,
        requested_type=MediaType.PHOTO,
        requester_id="agent-123"
    )
    response = await handler.request_media(request)
    if response.status == RequestStatus.COMPLETED:
        # Process photo content
        process_photo(response.decrypted_content)
```

**Performance Note**: This method loads and decrypts each media file to check its type. For large collections, this may be slow. Consider caching results if used frequently.

## Custom Protocol Implementation

You can create custom handlers by implementing the `MediaRequestProtocol`:

```python
from midori_ai_media_request import MediaRequest
from midori_ai_media_request import MediaRequestProtocol
from midori_ai_media_request import MediaResponse
from midori_ai_media_request import RequestStatus


class QueuedMediaRequestHandler(MediaRequestProtocol):
    \"\"\"Custom handler with request queueing.\"\"\"

    async def request_media(self, request: MediaRequest) -> MediaResponse:
        # Add to queue for async processing
        request_id = await self._add_to_queue(request)
        return MediaResponse(
            request_id=request_id,
            media_id=request.media_id,
            status=RequestStatus.PENDING,
        )

    async def get_request_status(self, request_id: str) -> MediaResponse:
        # Check queue status
        return await self._check_queue_status(request_id)

    async def cancel_request(self, request_id: str) -> bool:
        # Remove from queue
        return await self._remove_from_queue(request_id)
```

## Integration with Media Packages

This package integrates with:

- **midori-ai-media-vault**: Storage and encryption (provides MediaObject, MediaType, MediaCrypto)
- **midori-ai-media-lifecycle**: Decay management (provides LifecycleManager, should_parse, is_aged_out)

### Complete Example

```python
from pathlib import Path

from midori_ai_media_lifecycle import CleanupScheduler
from midori_ai_media_lifecycle import DecayConfig
from midori_ai_media_lifecycle import LifecycleManager

from midori_ai_media_request import MediaRequest
from midori_ai_media_request import MediaRequestHandler
from midori_ai_media_request import RequestPriority
from midori_ai_media_request import RequestStatus

from midori_ai_media_vault import MediaCrypto
from midori_ai_media_vault import MediaMetadata
from midori_ai_media_vault import MediaObject
from midori_ai_media_vault import MediaStorage
from midori_ai_media_vault import MediaType


async def full_workflow():
    # Setup storage and lifecycle
    storage = MediaStorage(base_path=Path("./media"))
    config = DecayConfig(full_probability_minutes=35.0, zero_probability_minutes=90.0)
    manager = LifecycleManager(storage=storage, config=config)

    # Create request handler
    handler = MediaRequestHandler(lifecycle_manager=manager)

    # Store some media
    content = b"image data..."
    encrypted, key, hash_str = MediaCrypto.encrypt(content)
    media = MediaObject(
        id="img-001",
        media_type=MediaType.PHOTO,
        metadata=MediaMetadata(content_hash=hash_str),
        user_id="user-123",
        encrypted_content=encrypted,
        encryption_key=key,
        content_integrity_hash=hash_str,
    )
    await storage.save(media)

    # Request the media
    request = MediaRequest(
        media_id="img-001",
        requested_type=MediaType.PHOTO,
        requester_id="agent-456",
        priority=RequestPriority.NORMAL,
    )
    response = await handler.request_media(request)

    if response.status == RequestStatus.COMPLETED:
        # Decrypted content is ready
        assert response.decrypted_content == content
        print(f"Successfully retrieved {len(response.decrypted_content)} bytes")
    elif response.status == RequestStatus.DENIED:
        print(f"Request denied: {response.denial_reason}")
        print(f"Parsing probability was: {response.parsing_probability:.1%}")
    elif response.status == RequestStatus.EXPIRED:
        print(f"Media expired: {response.denial_reason}")

    # Start background cleanup
    scheduler = CleanupScheduler(lifecycle_manager=manager, interval_seconds=300.0)
    scheduler.start()

    # ... application runs ...

    # Cleanup on shutdown
    await scheduler.stop()
```

## Error Handling

```python
from midori_ai_media_request import MediaRequest
from midori_ai_media_request import RequestStatus

from midori_ai_media_vault import MediaType


# Handle different response statuses
request = MediaRequest(
    media_id="photo-001",
    requested_type=MediaType.PHOTO,
    requester_id="agent-123",
)
response = await handler.request_media(request)

match response.status:
    case RequestStatus.COMPLETED:
        process_content(response.decrypted_content)
    case RequestStatus.DENIED:
        log_denial(response.denial_reason, response.parsing_probability)
    case RequestStatus.EXPIRED:
        log_expiration(response.denial_reason)
    case _:
        log_unexpected_status(response.status)
```

## Best Practices

1. **Check status before accessing content**: Always verify `status == COMPLETED` before using `decrypted_content`.

2. **Log denial reasons**: Track why requests fail to identify patterns or issues.

3. **Use appropriate priorities**: Reserve CRITICAL for time-sensitive operations.

4. **Include request reasons**: Helps with debugging and audit trails.

5. **Handle all statuses**: Don't assume success - always handle DENIED and EXPIRED cases.

## Type Validation

The handler enforces type matching between requested type and stored type:

```python
# This will be DENIED if media is actually VIDEO
request = MediaRequest(
    media_id="media-001",
    requested_type=MediaType.PHOTO,  # Must match stored type
    requester_id="agent-123",
)
response = await handler.request_media(request)

if response.status == RequestStatus.DENIED:
    # Response includes actual media type
    print(f"Expected {request.requested_type.value}, found {response.media_type.value}")
```
"""

# midori-ai-media-vault docs
MEDIA_VAULT_DOCS = """# midori-ai-media-vault Documentation

Encrypted media storage with Pydantic models for agent systems.

## Overview

This package provides secure media storage capabilities for agent systems, featuring:

- **Pydantic-based serialization** for type safety and validation
- **Per-file random Fernet encryption keys** stored alongside encrypted content
- **Onion/layered encryption**: Storage layer adds system-stats-derived encryption
- **Integrity verification** via SHA-256 hash of decrypted content
- **Support for multiple media types**: photos, videos, audio, text
- **100% async-friendly implementation**

## Quick Start

```python
import uuid

from pathlib import Path

from midori_ai_media_vault import MediaCrypto
from midori_ai_media_vault import MediaMetadata
from midori_ai_media_vault import MediaObject
from midori_ai_media_vault import MediaStorage
from midori_ai_media_vault import MediaType


async def example():
    # Create storage
    storage = MediaStorage(base_path=Path("./media_storage"))

    # Encrypt content with random key
    content = b"photo bytes here..."
    encrypted_content, encryption_key, integrity_hash = MediaCrypto.encrypt(content)

    # Create media object
    media = MediaObject(
        id=str(uuid.uuid4()),
        media_type=MediaType.PHOTO,
        metadata=MediaMetadata(content_hash=integrity_hash),
        user_id="user_12345",
        encrypted_content=encrypted_content,
        encryption_key=encryption_key,
        content_integrity_hash=integrity_hash,
    )

    # Save to disk
    await storage.save(media)

    # Load and decrypt
    loaded_media = await storage.load(media.id)
    decrypted = MediaCrypto.decrypt(
        loaded_media.encrypted_content,
        loaded_media.encryption_key,
        loaded_media.content_integrity_hash,
    )
    assert decrypted == content
```

## Data Models

### MediaType

Enum for supported media types:

```python
from midori_ai_media_vault import MediaType

MediaType.PHOTO  # "photo"
MediaType.VIDEO  # "video"
MediaType.AUDIO  # "audio"
MediaType.TEXT   # "text"
```

### MediaMetadata

Metadata tracking for media objects:

```python
from midori_ai_media_vault import MediaMetadata

metadata = MediaMetadata(
    content_hash="sha256-hash-of-raw-content",
)

# Auto-populated fields:
# - time_saved: datetime (default: now)
# - time_loaded: Optional[datetime]
# - time_parsed: Optional[datetime]
```

**Note:** Lifecycle management (ageout, decay) is handled by the `midori-ai-media-lifecycle` package, not the vault.

### MediaObject

Core media object with encrypted content:

```python
from midori_ai_media_vault import MediaObject

media = MediaObject(
    id="unique-media-id",
    media_type=MediaType.PHOTO,
    metadata=MediaMetadata(content_hash="..."),
    user_id="owner-user-id",
    encrypted_content=b"encrypted-bytes",
    encryption_key=b"fernet-key",
    content_integrity_hash="sha256-of-decrypted-content",
)
```

## Encryption

### MediaCrypto

Static methods for per-file encryption:

```python
from midori_ai_media_vault import MediaCrypto

# Encrypt data with a new random key
encrypted, key, hash = MediaCrypto.encrypt(b"raw content")

# Decrypt data and verify integrity
decrypted = MediaCrypto.decrypt(encrypted, key, hash)
```

### Encryption Approach

- Each media file uses a **unique random Fernet key**
- The key is stored in the Pydantic model alongside encrypted content
- Integrity is verified via SHA-256 hash on decrypt
- No key derivation complexity - keys are randomly generated

## Storage

### MediaStorage

Async disk storage with Pydantic JSON serialization and onion encryption:

```python
from pathlib import Path

from midori_ai_media_vault import MediaStorage

# Initialize storage (uses system-stats encryption by default with 12 iterations)
storage = MediaStorage(base_path=Path("./media_storage"))

# Custom iterations for key derivation
storage = MediaStorage(base_path=Path("./media_storage"), system_key_iterations=12)

# Save media (writes encrypted to {base_path}/{id}.media)
await storage.save(media)

# Load media by ID
loaded = await storage.load("media-id")

# Delete media
deleted = await storage.delete("media-id")  # Returns True if deleted

# Check if media exists
exists = await storage.exists("media-id")

# List all media IDs
ids = await storage.list_all()

# List media IDs filtered by type
photo_ids = await storage.list_by_type(MediaType.PHOTO)
audio_ids = await storage.list_by_type(MediaType.AUDIO)
```

#### list_by_type Performance Note

The `list_by_type()` method is optimized to simply list files in the type-specific folder (e.g., `photo/`, `video/`), without needing to load or decrypt any files. This makes it very fast even for large collections.

```python
# Fast operation - just lists folder contents
photo_ids = await storage.list_by_type(MediaType.PHOTO)
for photo_id in photo_ids:
    media = await storage.load(photo_id)
    # Process media...
```

### Storage Format and Folder Structure

Media objects are organized into type-specific subfolders for optimized filtering:

```
base_path/
├── photo/
│   ├── photo-1.media
│   └── photo-2.media
├── video/
│   └── video-1.media
├── audio/
│   └── audio-1.media
└── text/
    └── text-1.media
```

Each `.media` file contains the serialized MediaObject JSON encrypted using a system-stats-derived key.

### Onion/Layered Encryption

The storage uses two layers of encryption (like Tor/onion routing):

1. **Inner layer**: Media content is encrypted with a per-file random Fernet key (stored in MediaObject)
2. **Outer layer**: The entire MediaObject JSON is encrypted with a system-stats-derived key when saving

This provides defense-in-depth: even if storage files are copied to another system, they cannot be decrypted without matching system stats.

### SystemCrypto

The system-stats encryption uses stable hardware characteristics that are unlikely to change over 90 minutes:

```python
from midori_ai_media_vault import SystemCrypto, get_system_stats, derive_system_key

# Get raw system stats string
stats = get_system_stats()
# Returns: "total_memory|cpu_count|processor|machine|system"

# Derive a Fernet key from system stats
key = derive_system_key(iterations=12)  # 12 SHA-256 iterations

# Use SystemCrypto directly
crypto = SystemCrypto(iterations=12)
encrypted = crypto.encrypt(b"data")
decrypted = crypto.decrypt(encrypted)
```

System stats collected:
- Total memory (NOT free/used memory)
- CPU count (logical)
- CPU processor/name
- Machine architecture
- Operating system

## Best Practices

1. **Always verify integrity**: Use `MediaCrypto.decrypt()` which automatically verifies the hash.

2. **Store encryption keys securely**: While keys are stored with the data for simplicity, consider additional security measures for production.

3. **Use async operations**: All storage operations are async-friendly for non-blocking I/O.

4. **Manage lifecycle externally**: This package handles storage only. Use `midori-ai-media-lifecycle` to configure retention policies and cleanup schedules.

## Error Handling

```python
from midori_ai_media_vault import MediaCrypto

try:
    decrypted = MediaCrypto.decrypt(encrypted, key, expected_hash)
except ValueError as e:
    # Content integrity check failed - data may be corrupted
    print(f"Integrity error: {e}")
```

## Integration with Other Packages

This package is designed as the foundation for the media storage family:

- **midori-ai-media-lifecycle**: Time-based decay and parsing scheduler (depends on this package)
- **midori-ai-media-request**: Type-safe request/response interface for agents (depends on this package)
"""

# midori-ai-mood-engine docs
MOOD_ENGINE_DOCS = """# Midori AI Mood Engine - Documentation

Comprehensive mood management system with hormone simulation, loneliness tracking, energy modeling, and PyTorch-based self-retraining.

## Features

- **Hormone Simulation**: 28+ hormones across reproductive, stress, mood, and metabolism categories with 28-day cycle support
- **Loneliness Tracking**: Time-since-interaction tracking, social need accumulation, connection quality scoring
- **Energy Modeling**: Base energy tracking, activity expenditure, rest recovery, circadian rhythm integration
- **Unified Mood API**: Single interface returning energy, happiness, irritability, anxiety, focus, loneliness, etc.
- **Self-Retraining**: PyTorch model learns from feedback, adjusts response curves based on observed mood outcomes
- **Profile Configuration**: Gender, age, modifier intensity, feature toggles

## Installation

```bash
uv add midori-ai-mood-engine
```

## Core Concepts

### MoodEngine

The main entry point for the mood system. It combines all subsystems into a unified interface.

```python
from midori_ai_mood_engine import MoodEngine, StepType
from datetime import datetime
import pytz

tz = pytz.timezone('America/Los_Angeles')
engine = MoodEngine(
    cycle_start=datetime(2008, 4, 15, tzinfo=tz),
    step_type=StepType.FULL
)
```

### Resolution Modes (StepType)

- `StepType.DAY`: 28 daily steps (fastest, least precise)
- `StepType.PULSE`: 448 steps (90-minute pulses over 28 days)
- `StepType.FULL`: 80,640 steps (30-second intervals, most precise)

### MoodState

Represents a snapshot of the current mood with these attributes:
- `energy`: Physical and mental energy level
- `happiness`: General sense of well-being
- `irritability`: Tendency to react negatively
- `anxiety`: Nervousness and worry
- `focus`: Ability to concentrate
- `loneliness`: Sense of social isolation
- `mood_swings`: Volatility of emotional state
- `libido`: Sexual drive
- `sleep_quality`: Quality of recent sleep
- `social_need`: Desire for social interaction

## Impact System API

Apply external events that affect mood state:

### `apply_stress(intensity: float) -> MoodState`
Apply stress impact. Raises cortisol and adrenaline effects.
- `intensity`: 0.0 to 1.0

### `apply_relaxation(intensity: float) -> MoodState`
Apply relaxation impact. Raises oxytocin and serotonin effects.
- `intensity`: 0.0 to 1.0

### `apply_exercise(intensity: float, duration_minutes: float) -> MoodState`
Apply exercise impact. Raises endorphins, testosterone, depletes energy.
- `intensity`: 0.0 to 1.0
- `duration_minutes`: Duration of exercise

### `apply_meal(meal_type: MealType) -> MoodState`
Apply meal impact. Affects insulin, leptin, ghrelin.
- `meal_type`: `MealType.BREAKFAST`, `LUNCH`, `DINNER`, `SNACK`, `HEAVY`, `LIGHT`

### `apply_sleep_deprivation(hours: float) -> MoodState`
Apply sleep deprivation impact.
- `hours`: Hours of sleep missed

### `apply_social_interaction(quality: float, duration_minutes: float) -> MoodState`
Apply social interaction impact. Reduces loneliness, raises oxytocin.
- `quality`: 0.0 to 1.0 (quality of interaction)
- `duration_minutes`: Duration of interaction

### `apply_rest(hours: float) -> MoodState`
Apply rest impact. Restores energy, balances hormones.
- `hours`: Hours of rest

## Self-Retraining System

The engine can learn from feedback to adjust its response curves:

```python
# Collect feedback
feedback = [
    {"predicted": {"happiness": 0.7}, "actual": {"happiness": 0.5}},
    {"predicted": {"energy": 0.6}, "actual": {"energy": 0.8}},
]

# Retrain model
result = engine.retrain(feedback)
print(f"Retrained with {result['samples']} samples, final loss: {result['final_loss']:.4f}")

# Save model (async, encrypted with system-derived key - 12 iterations)
await engine.save_model("mood_engine.pt")

# Load model (async, decrypted with system-derived key)
await engine.load_model("mood_engine.pt")
```

**Security Note**: Model persistence uses the `midori-ai-media-vault` encryption system with 12 iterations of system-stats-derived key hashing. This ensures models are encrypted at rest using system-specific keys.

## Profile Configuration

Configure the engine for different profiles:

```python
from midori_ai_mood_engine import MoodProfile, Gender

profile = MoodProfile(
    gender=Gender.FEMALE,      # FEMALE, MALE, or CUSTOM
    age=25,                    # Affects baseline hormone levels
    modifier=1.0,              # Global intensity multiplier
    cycle_enabled=True,        # Enable menstrual cycle
    loneliness_enabled=True,   # Enable loneliness tracking
    energy_enabled=True        # Enable energy simulation
)
```

## TOML Configuration

```toml
[mood_engine]
cycle_start = "2008-04-15T00:00:00"
timezone = "America/Los_Angeles"
default_step_type = "full"

[mood_engine.profile]
gender = "female"
age = 25
modifier = 1.0
cycle_enabled = true
loneliness_enabled = true
energy_enabled = true

[mood_engine.training]
auto_retrain = true
retrain_interval_hours = 24
min_feedback_samples = 100
```

Load configuration:

```python
from midori_ai_mood_engine import MoodEngine, load_config_from_toml

config = load_config_from_toml("config.toml")
engine = MoodEngine(config=config)
```

## Hormone Categories

### Reproductive (14 hormones)
- GnRH, FSH, LH, Estradiol, Progesterone
- Inhibin A, Inhibin B, Activin, AMH
- Prolactin, hCG, Relaxin, Testosterone, DHEA

### Stress (3 hormones)
- Cortisol, Adrenaline, Norepinephrine

### Mood (6 hormones)
- Melatonin, Serotonin, Dopamine
- Oxytocin, GABA, Endorphins

### Metabolism (5 hormones)
- Insulin, Leptin, Ghrelin, T3, T4

## API Reference

### MoodEngine

```python
class MoodEngine:
    def get_mood_at_datetime(current_time: datetime) -> MoodState
    def get_current_mood() -> MoodState
    def get_hormone_levels(current_time: datetime = None) -> dict[str, float]
    def is_on_period(current_time: datetime = None) -> tuple[bool, float]
    def apply_stress(intensity: float) -> MoodState
    def apply_relaxation(intensity: float) -> MoodState
    def apply_exercise(intensity: float, duration_minutes: float) -> MoodState
    def apply_meal(meal_type: MealType) -> MoodState
    def apply_sleep_deprivation(hours: float) -> MoodState
    def apply_social_interaction(quality: float, duration_minutes: float) -> MoodState
    def apply_rest(hours: float) -> MoodState
    def retrain(feedback_data: list[dict] = None) -> dict[str, float]
    async def save_model(path: str, metadata: dict = None) -> None
    async def load_model(path: str) -> dict[str, Any]
```

## Notes

- The hardcoded cycle start date (2008-04-15) is a specific reference point for backward compatibility
- PyTorch is required for self-retraining capability
- All persistence methods (save_model, load_model) are async and non-blocking
- Model files are encrypted using system-stats-derived keys (12 iterations) via midori-ai-media-vault
- Energy subsystem uses circadian rhythm for realistic energy patterns
"""

# midori-ai-reranker docs
RERANKER_DOCS = """# Midori AI Reranker - Detailed Documentation

LangChain-powered reranking utilities for Midori AI vector storage with filter pipelines, threshold configuration, and optional LLM-based reranking.

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Basic Usage](#basic-usage)
4. [Threshold Configuration](#threshold-configuration)
5. [Custom Filter Pipelines](#custom-filter-pipelines)
6. [Optional LLM Reranking](#optional-llm-reranking)
7. [Embedding Providers](#embedding-providers)
8. [API Reference](#api-reference)

## Overview

When retrieving vectors from storage, raw similarity search results often need refinement:

1. **Relevance filtering** - Remove results below a similarity threshold
2. **Redundancy removal** - Filter out near-duplicate content
3. **Sender prioritization** - Prioritize user content vs model content for better LLM/LRM context
4. **LLM-based reranking** - Use an LLM to intelligently reorder results (optional, heavyweight)

This package wraps LangChain's document transformers with a Midori AI-friendly interface:

- Uses `EmbeddingsRedundantFilter` and `EmbeddingsFilter` for fast, filter-based reranking
- Uses `DocumentCompressorPipeline` for chaining filters
- Uses `InMemoryVectorStore` pattern for efficient temporary storage
- Supports configurable thresholds with per-query modifiers
- Integrates with `midori-ai-agent-base` for optional LLM-based reranking
- Works with `midori-ai-vector-manager` types (`VectorEntry`, `SenderType`)

**Key Design Principles:**

- **LangChain-powered** - Leverage battle-tested LangChain document transformers
- **Filter-first architecture** - Prioritize fast embedding-based filters over slow LLM reranking
- **Pipeline composition** - Use `DocumentCompressorPipeline` for chaining filters
- **Threshold configurability** - Support per-query threshold modifiers (base + modifier)
- **Async-first** - Use LangChain's async methods (`ainvoke`, `afrom_texts`)
- **BYOB (Bring Your Own Backend)** - Users provide their own embedding/LLM endpoints

## Installation

All embedding providers (OpenAI, Ollama, LocalAI, HuggingFace) are included by default.

```bash
# Using UV
uv add "git+https://github.com/Midori-AI-OSS/Carly-AGI#subdirectory=Rest-Servers/packages/midori-ai-reranker"

# Using Pip
pip install "git+https://github.com/Midori-AI-OSS/Carly-AGI#subdirectory=Rest-Servers/packages/midori-ai-reranker"
```

## Basic Usage

### Production Pattern

```python
from midori_ai_reranker import DocumentReranker, get_localai_embeddings

# Configure embeddings (OpenAI-compatible endpoint)
embeddings = get_localai_embeddings(
    api_key="your-api-key",
    model="text-embedding-ada-002",
    base_url="http://localhost:8080/v1"
)

# Create reranker with the production filter pipeline
reranker = DocumentReranker(
    embeddings=embeddings,
    relevance_threshold=0.2  # Base threshold
)

# Rerank a list of text items
question = "What did the user ask about?"
raw_items = ["memory text 1", "memory text 2", "duplicate of 1", ...]

reranked_items = await reranker.rerank(
    question=question,
    items=raw_items,
    similarity_threshold_mod=0.0  # Optional per-query adjustment
)
```

### Using OpenAI Embeddings

```python
from midori_ai_reranker import DocumentReranker, get_openai_embeddings

# Direct OpenAI API
embeddings = get_openai_embeddings(
    api_key="your-openai-api-key",
    model="text-embedding-3-small"
)

reranker = DocumentReranker(embeddings=embeddings)

reranked_items = await reranker.rerank(
    question="What is the capital of France?",
    items=["Paris is the capital", "London is in England", "Paris has the Eiffel Tower"]
)
```

### Using Ollama Embeddings

```python
from midori_ai_reranker import DocumentReranker, get_ollama_embeddings

# Local Ollama server
embeddings = get_ollama_embeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434"
)

reranker = DocumentReranker(embeddings=embeddings)

reranked_items = await reranker.rerank(
    question="Tell me about Python",
    items=["Python is a programming language", "Snakes are reptiles", "Python has great libraries"]
)
```

## Threshold Configuration

The relevance threshold is calculated as: **`effective_threshold = base_threshold + similarity_threshold_mod`**

- **Base threshold:** 0.2 (default, set during reranker initialization)
- **Threshold modifier:** 0.0 (default, can be adjusted per-query)

### Using Threshold Modifiers

```python
from midori_ai_reranker import DocumentReranker, get_openai_embeddings

embeddings = get_openai_embeddings(
    api_key="your-api-key",
    model="text-embedding-3-small"
)

reranker = DocumentReranker(
    embeddings=embeddings,
    relevance_threshold=0.2  # Base threshold
)

# For user-specific memory queries, use higher threshold
reranked_items = await reranker.rerank(
    question="What did I say earlier?",
    items=raw_items,
    similarity_threshold_mod=0.3  # 0.2 base + 0.3 = 0.5 effective threshold
)

# For web/general queries, use lower threshold
reranked_items = await reranker.rerank(
    question="General information about topic",
    items=raw_items,
    similarity_threshold_mod=0.0  # 0.2 base + 0.0 = 0.2 effective threshold
)
```

### Advanced Configuration

```python
from midori_ai_reranker import DocumentReranker, RerankerConfig, get_openai_embeddings

embeddings = get_openai_embeddings(
    api_key="your-api-key",
    model="text-embedding-3-small"
)

# Create custom config
config = RerankerConfig(
    relevance_threshold=0.3,          # Higher base threshold
    max_items=100,                     # Process more items
    enable_redundant_filter=True,      # Enable duplicate removal
    enable_relevance_filter=True       # Enable relevance filtering
)

reranker = DocumentReranker(embeddings=embeddings, config=config)

reranked_items = await reranker.rerank(
    question="Search query",
    items=raw_items
)
```

## Custom Filter Pipelines

Build custom filter chains with `FilterPipeline`:

```python
from midori_ai_reranker import FilterPipeline, RedundantFilter, RelevanceFilter, get_openai_embeddings

embeddings = get_openai_embeddings(
    api_key="your-api-key",
    model="text-embedding-3-small"
)

# Build custom pipeline (order matters!)
pipeline = FilterPipeline(
    embeddings=embeddings,
    filters=[
        RedundantFilter(embeddings),              # Remove duplicates first
        RelevanceFilter(embeddings, threshold=0.3), # Then filter by relevance
    ]
)

reranked = await pipeline.compress(
    query="What is machine learning?",
    documents=raw_items,
    max_results=10  # Limit to top 10
)
```

### Filter Order Matters

**Recommended order:** `RedundantFilter` → `RelevanceFilter`

1. Remove duplicates first (faster, reduces items for next filter)
2. Then filter by relevance (operates on deduplicated set)

## Optional LLM Reranking

LLM-based reranking is **optional and expensive**. Use it sparingly when embedding-based filters are insufficient.

```python
from midori_ai_reranker import FilterPipeline, RedundantFilter, RelevanceFilter, LLMReranker, get_openai_embeddings
from midori_ai_agent_base import get_agent

# Set up embeddings
embeddings = get_openai_embeddings(
    api_key="your-api-key",
    model="text-embedding-3-small"
)

# Use Midori AI agent base factory
agent = await get_agent(
    backend="langchain",
    model="groq/compound",
    api_key="your-groq-api-key",
    base_url="https://api.groq.com/openai/v1",
    temperature=0.1,
    use_responses_api=True
)

# Create LLM reranker using the agent
llm_reranker = LLMReranker(agent=agent)

# Add to pipeline after filters (optional, expensive)
pipeline = FilterPipeline(
    embeddings=embeddings,
    filters=[
        RedundantFilter(embeddings),
        RelevanceFilter(embeddings, threshold=0.2),
        llm_reranker,  # Optional final LLM pass
    ]
)

# Note: LLMReranker does NOT integrate with DocumentCompressorPipeline
# Use it separately for custom reranking logic
documents = ["doc1", "doc2", "doc3"]
reranked = await llm_reranker.rerank(
    query="What is the most relevant document?",
    documents=documents,
    top_k=5
)
```

## Embedding Providers

### OpenAI

```python
from midori_ai_reranker import get_openai_embeddings

# Direct OpenAI API
embeddings = get_openai_embeddings(
    api_key="your-openai-api-key",
    model="text-embedding-3-small"
)

# Custom base URL (e.g., Azure OpenAI)
embeddings = get_openai_embeddings(
    api_key="your-api-key",
    model="text-embedding-ada-002",
    base_url="https://your-resource.openai.azure.com/openai/deployments/your-deployment"
)
```

### Ollama

```python
from midori_ai_reranker import get_ollama_embeddings

# Local Ollama server
embeddings = get_ollama_embeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434"
)
```

### LocalAI (OpenAI-Compatible)

```python
from midori_ai_reranker import get_localai_embeddings

# Any OpenAI-compatible endpoint
embeddings = get_localai_embeddings(
    api_key="your-api-key",
    model="text-embedding-ada-002",
    base_url="http://localhost:8080/v1",
    max_retries=1,
    request_timeout=75
)
```

### HuggingFace

```python
from midori_ai_reranker import get_huggingface_embeddings

# Local or HuggingFace Inference API
embeddings = get_huggingface_embeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# With custom model kwargs
embeddings = get_huggingface_embeddings(
    model_name="sentence-transformers/all-mpnet-base-v2",
    model_kwargs={"device": "cuda"}
)
```

## API Reference

### DocumentReranker

Main class for document reranking with configurable filters.

```python
DocumentReranker(
    embeddings: Embeddings,
    relevance_threshold: float = 0.2,
    config: Optional[RerankerConfig] = None
)
```

**Parameters:**
- `embeddings`: Embeddings function for similarity comparison
- `relevance_threshold`: Base relevance threshold (default 0.2)
- `config`: Optional RerankerConfig for advanced settings

**Methods:**

```python
async def rerank(
    question: str,
    items: list[str],
    similarity_threshold_mod: float = 0.0,
    max_results: Optional[int] = None
) -> list[str]
```

### FilterPipeline

Custom filter pipeline for document compression.

```python
FilterPipeline(
    embeddings: Embeddings,
    filters: Optional[list] = None
)
```

**Parameters:**
- `embeddings`: Embeddings function for similarity comparison
- `filters`: Optional list of filter components (RedundantFilter, RelevanceFilter, etc.)

**Methods:**

```python
async def compress(
    query: str,
    documents: list[str],
    max_results: Optional[int] = None
) -> list[str]
```

### RerankerConfig

Configuration dataclass for reranker settings.

```python
@dataclass
class RerankerConfig:
    relevance_threshold: float = 0.2
    similarity_threshold_mod: float = 0.0
    max_items: int = 50
    enable_redundant_filter: bool = True
    enable_relevance_filter: bool = True
```

### RedundantFilter

Wrapper for LangChain's `EmbeddingsRedundantFilter`.

```python
RedundantFilter(
    embeddings: Embeddings,
    similarity_threshold: float = 0.95
)
```

### RelevanceFilter

Wrapper for LangChain's `EmbeddingsFilter`.

```python
RelevanceFilter(
    embeddings: Embeddings,
    threshold: float = 0.2
)
```

**Methods:**

```python
def update_threshold(new_threshold: float) -> None
```

### LLMReranker

Optional LLM-based reranking using Midori AI agent base.

```python
LLMReranker(agent: MidoriAiAgentProtocol)
```

**Methods:**

```python
async def rerank(
    query: str,
    documents: list[str],
    top_k: Optional[int] = None
) -> list[str]
```

## LangChain Components Reference

| Component | Import Path | Purpose |
|-----------|-------------|---------|
| `EmbeddingsRedundantFilter` | `langchain_community.document_transformers` | Remove duplicate documents |
| `EmbeddingsFilter` | `langchain.retrievers.document_compressors.embeddings_filter` | Filter by relevance threshold |
| `DocumentCompressorPipeline` | `langchain.retrievers.document_compressors.base` | Chain filters together |
| `ContextualCompressionRetriever` | `langchain.retrievers` | Orchestrate compression with retriever |
| `InMemoryVectorStore` | `langchain_community.vectorstores` | Temporary store for raw results |

## Performance Notes

- **Filter-based reranking** (default) is fast and cost-effective
- **LLM-based reranking** is slow and expensive - use sparingly
- **Default max_items** is 50 (performance/cost tradeoff)
- **Filter order** matters: redundant → relevance is optimal
- **Threshold tuning**: Start with 0.2, adjust based on precision/recall needs

## Examples

See the [examples directory](./examples) for more usage patterns and integration examples.
"""

# midori-ai-vector-manager docs
VECTOR_MANAGER_DOCS = """# midori-ai-vector-manager Documentation

## Overview

`midori-ai-vector-manager` provides a reusable, protocol-based vector storage abstraction for Midori AI packages. It extracts the ChromaDB wrapper into a standalone package that any component can use.

## Features

- **Protocol-based design**: `VectorStoreProtocol` ABC allows future backend support
- **ChromaDB backend**: Full-featured ChromaDB implementation
- **Multimodal support**: Text and image storage via OpenCLIP
- **Sender tracking**: `SenderType` enum for reranking support
- **Standard persistence**: Default path `~/.midoriai/vectorstore/{backend}/`
- **Flexible embeddings**: Support ChromaDB defaults or custom OpenAI-friendly models
- **Long-term storage**: Optional `disable_time_gating` flag for permanent knowledge storage
- **100% async-friendly**: All operations are async-compatible

## Installation

```bash
uv add midori-ai-vector-manager
```

## API Reference

### Enums

#### SenderType

```python
from midori_ai_vector_manager import SenderType

class SenderType(str, Enum):
    USER = "user"      # Content from user
    MODEL = "model"    # Content from model
    SYSTEM = "system"  # System-generated content
```

### Models

#### VectorEntry

```python
from midori_ai_vector_manager import VectorEntry

entry = VectorEntry(
    id="1234567890-abc12345",
    text="The stored text content",
    timestamp=1699999999.0,
    sender=SenderType.USER,
    metadata={"session_id": "user123"}
)

# Get age in minutes
age = entry.age_minutes

# Convert to ChromaDB metadata format
chroma_meta = entry.to_chromadb_metadata()
```

### Protocol

#### VectorStoreProtocol

All backends implement this protocol:

```python
class VectorStoreProtocol(ABC):
    async def store(self, text: str, sender: Optional[SenderType] = None, metadata: Optional[dict[str, Any]] = None) -> VectorEntry
    async def get_by_id(self, entry_id: str) -> Optional[VectorEntry]
    async def query(self, filters: dict[str, Any], limit: int = 100) -> list[VectorEntry]
    async def search_similar(self, query_text: str, limit: int = 10) -> list[VectorEntry]
    async def delete(self, entry_ids: list[str]) -> int
    async def count(self) -> int
    async def clear(self) -> None
```

### Backends

#### ChromaVectorStore

Text-only vector storage with ChromaDB:

```python
from midori_ai_vector_manager import ChromaVectorStore, SenderType

# Create store with default persistence path (~/.midoriai/vectorstore/chromadb/)
store = ChromaVectorStore(collection_name="my_collection")

# Or with custom path
store = ChromaVectorStore(
    collection_name="my_collection",
    persist_directory="/custom/path"
)

# Or disable time gating for long-term storage
long_term_store = ChromaVectorStore(
    collection_name="long_term_knowledge",
    disable_time_gating=True  # Entries use simple UUIDs without timestamps
)

# Store text with sender metadata
entry = await store.store(
    text="This is my reasoning about the problem...",
    sender=SenderType.MODEL,
    metadata={"session_id": "user123", "model": "preprocessing"}
)

# Query by metadata
entries = await store.query(
    filters={"session_id": "user123"},
    limit=50
)

# Semantic similarity search
similar = await store.search_similar(
    query_text="What did the user ask about?",
    limit=10
)

# Delete entries
deleted_count = await store.delete([entry.id for entry in entries])

# Get entry by ID
entry = await store.get_by_id("1234567890-abc12345")

# Count entries
total = await store.count()

# Clear all entries
await store.clear()
```

#### ChromaMultimodalStore

Image storage with OpenCLIP embeddings:

```python
from midori_ai_vector_manager import ChromaMultimodalStore

# Create multimodal store
image_store = ChromaMultimodalStore(collection_name="user_images")

# Store an image
entry = await image_store.store_image(
    image_data=image_bytes,
    metadata={"user_id": "123", "description": "selfie"}
)

# Query images by text
results = await image_store.query_by_text(
    query_text="animals",
    limit=5
)
```

### Custom Embedding Functions

Use custom OpenAI-friendly embedding models:

```python
from midori_ai_vector_manager import ChromaVectorStore
from chromadb.utils import embedding_functions

# Use OpenAI embeddings
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key="your-api-key",
    model_name="text-embedding-ada-002"
)

store = ChromaVectorStore(
    collection_name="my_collection",
    embedding_function=openai_ef
)

# Or use any OpenAI-compatible endpoint (LocalAI, etc.)
localai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_base="http://localhost:8080/v1",
    api_key="not-needed",
    model_name="text-embedding-ada-002"
)

store = ChromaVectorStore(
    collection_name="my_collection",
    embedding_function=localai_ef
)
```

## Configuration

### Default Persistence Path

The default persistence path is `~/.midoriai/vectorstore/{backend}/`. For ChromaDB, this becomes `~/.midoriai/vectorstore/chromadb/`.

You can override this with the `persist_directory` parameter:

```python
store = ChromaVectorStore(
    collection_name="my_collection",
    persist_directory="/custom/path/to/storage"
)
```

### Ephemeral Storage

For in-memory storage (no persistence), pass `None` as `persist_directory`:

```python
store = ChromaVectorStore(
    collection_name="my_collection",
    persist_directory=None  # Ephemeral storage
)
```

## Integration Example

### Using with midori-ai-context-bridge

```python
from midori_ai_vector_manager import ChromaVectorStore, VectorEntry

# context-bridge creates its store using vector-manager
reasoning_store = ChromaVectorStore(
    collection_name="reasoning_cache",
    # Uses standard path: ~/.midoriai/vectorstore/chromadb/
)

# Store reasoning with sender tracking
entry = await reasoning_store.store(
    text="Preprocessing: Analyzed user intent...",
    sender=SenderType.MODEL,
    metadata={"session_id": "user:123", "model_type": "preprocessing"}
)

# Retrieve similar reasoning
similar = await reasoning_store.search_similar(
    query_text="user intent analysis",
    limit=5
)
```

## LanceDB Backend

LanceDB provides an alternative vector storage backend with columnar format storage:

```python
from midori_ai_vector_manager import LanceVectorStore, SenderType

# Create store with default persistence path (~/.midoriai/vectorstore/lancedb/)
store = LanceVectorStore(table_name="my_table")

# Or with custom path
store = LanceVectorStore(
    table_name="my_table",
    persist_directory="/custom/path"
)

# Store text with sender metadata
entry = await store.store(
    text="This is my reasoning about the problem...",
    sender=SenderType.MODEL,
    metadata={"session_id": "user123"}
)

# Semantic similarity search
similar = await store.search_similar(
    query_text="What did the user ask about?",
    limit=10
)
```

## Backend Comparison

| Database | Status | Notes |
|----------|--------|-------|
| ChromaDB | **Implemented** | CPU-based embeddings, good defaults |
| LanceDB | **Implemented** | Columnar format, fast analytics |
| Qdrant | Future | Production-ready, advanced filtering |
| Milvus | Not recommended | Complex setup, overkill for most uses |
"""

def list_all_docs() -> dict[str, str]:
    """
    Return a dictionary of all embedded documentation.
    
    Returns:
        dict[str, str]: Package names mapped to their documentation strings
    """
    return {
        "midori-ai-agent-base": AGENT_BASE_DOCS,
        "midori-ai-agent-context-manager": AGENT_CONTEXT_MANAGER_DOCS,
        "midori-ai-agent-huggingface": AGENT_HUGGINGFACE_DOCS,
        "midori-ai-agent-langchain": AGENT_LANGCHAIN_DOCS,
        "midori-ai-agent-openai": AGENT_OPENAI_DOCS,
        "midori-ai-compactor": COMPACTOR_DOCS,
        "midori-ai-context-bridge": CONTEXT_BRIDGE_DOCS,
        "midori-ai-media-lifecycle": MEDIA_LIFECYCLE_DOCS,
        "midori-ai-media-request": MEDIA_REQUEST_DOCS,
        "midori-ai-media-vault": MEDIA_VAULT_DOCS,
        "midori-ai-mood-engine": MOOD_ENGINE_DOCS,
        "midori-ai-reranker": RERANKER_DOCS,
        "midori-ai-vector-manager": VECTOR_MANAGER_DOCS,
    }
