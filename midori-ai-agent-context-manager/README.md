# Midori AI Agent Context Manager

Context management for Midori AI agent backends with Pydantic persistence.

## Features

- **In-memory conversation history**: Track user messages, assistant responses, system prompts, and tool calls
- **Async file persistence**: Save and load memory to/from JSON files using Pydantic serialization
- **Flexible entry types**: Support for user, assistant, system, and tool messages
- **Metadata support**: Attach arbitrary metadata to entries and the overall memory store
- **Memory trimming**: Optional max entry limit with automatic oldest-first removal
- **Summary support**: Store conversation summaries for long-running sessions
- **Auto-compression**: Automatic memory compression when context window limits are approached

## Installation

```bash
uv add midori-ai-agent-context-manager
```

## Quick Start

```python
from midori_ai_agent_context_manager import MemoryStore, ToolCallEntry

# Create a memory store for an agent
memory = MemoryStore(agent_id="my-agent")

# Add messages
memory.add_user_message("What's the weather like?")
memory.add_assistant_message("Let me check that for you.", tool_calls=[
    ToolCallEntry(name="get_weather", args={"location": "NYC"}, result="Sunny, 72°F")
])
memory.add_assistant_message("It's sunny and 72°F in NYC!")

# Save to file
await memory.save("/path/to/memory.json")

# Load from file later
memory2 = MemoryStore(agent_id="my-agent")
await memory2.load("/path/to/memory.json")
```

## API Reference

### MemoryStore

The main class for managing agent memory.

```python
store = MemoryStore(agent_id="my-agent", max_entries=100)
```

**Methods:**

- `add_user_message(content, metadata=None)` - Add a user message
- `add_assistant_message(content, tool_calls=None, metadata=None)` - Add an assistant message
- `add_system_message(content, metadata=None)` - Add a system message
- `add_tool_result(tool_name, result, call_id=None, metadata=None)` - Add a tool result
- `get_recent_entries(count)` - Get the N most recent entries
- `get_entries_since(timestamp)` - Get entries after a timestamp
- `clear()` - Remove all entries
- `async save(file_path=None)` - Save to JSON file
- `async load(file_path)` - Load from JSON file

**Properties:**

- `agent_id` - The agent's identifier
- `entries` - List of memory entries (copy)
- `summary` - Optional conversation summary
- `metadata` - Store-level metadata (copy)

### Models

- `MemoryEntry` - A single conversation entry
- `MemorySnapshot` - Complete serializable memory state
- `ToolCallEntry` - Tool call with name, args, result
- `MessageRole` - Enum: USER, ASSISTANT, SYSTEM, TOOL
- `CompressionConfig` - Configuration for memory auto-compression
- `MemoryCompressor` - Handles automatic memory compression

## Auto-Compression

Automatically compress memory when approaching context window limits:

```python
from midori_ai_agent_context_manager import MemoryStore, MemoryCompressor, CompressionConfig

# Create a compression config (uses 80% threshold by default)
config = CompressionConfig(
    model_name="gpt-oss-120b",  # Automatically looks up 131k context window
    compression_threshold=0.8   # Compress at 80% of context window
)

# Define a summarizer using your LLM
async def summarize_with_llm(text: str) -> str:
    # Use your agent/LLM to generate the summary
    response = await your_llm.invoke(text)
    return response

# Create compressor
compressor = MemoryCompressor(config=config, summarizer=summarize_with_llm)

# Check and compress if needed
memory = MemoryStore(agent_id="my-agent")
# ... add messages ...

entries, was_compressed = await compressor.compress_if_needed(
    entries=memory.entries,
    system_context="You are a helpful assistant."
)
```

### Known Model Context Windows

The package includes preset context windows for known gpt-oss models (in thousands of tokens):

- `gpt-oss-120b`, `gpt-oss-20b`: 131k tokens

You can also set a custom context window explicitly (in thousands of tokens):

```python
config = CompressionConfig(context_window=65)  # 65k tokens
```
