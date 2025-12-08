# Midori AI Agent Context Manager Documentation

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
