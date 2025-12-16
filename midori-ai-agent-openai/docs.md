# midori-ai-agent-openai Documentation

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
- Includes a compatibility patch for the `Usage` class to handle `None` values in `input_tokens_details` and `output_tokens_details` fields, preventing Pydantic validation errors when using backends that don't provide these optional fields

## Known Issues and Fixes

### Usage Type Validation Errors

The `openai-agents` library's `Usage` type expects `input_tokens_details` and `output_tokens_details` to be valid dictionary or model instances. Some OpenAI-compatible backends (like Ollama, LocalAI, or older OpenAI API versions) may return `None` for these fields, causing Pydantic validation errors:

```
Error: 2 validation errors for Usage
input_tokens_details
  Input should be a valid dictionary or instance of InputTokensDetails
output_tokens_details
  Input should be a valid dictionary or instance of OutputTokensDetails
```

This package includes an automatic fix that monkey-patches the `Usage.__init__` method to replace `None` values with properly initialized default instances (`InputTokensDetails(cached_tokens=0)` and `OutputTokensDetails(reasoning_tokens=0)`). This patch is applied automatically when the adapter module is imported.

## Reference

See the Swarm-o-codex project for advanced agent patterns:
https://github.com/Midori-AI-OSS/Midori-AI/tree/main/Experimentation/Swarm-o-codex
