# midori-ai-agent-base Documentation

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
