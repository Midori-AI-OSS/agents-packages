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

## Reference

See the Swarm-o-codex project for advanced agent patterns:
https://github.com/Midori-AI-OSS/Midori-AI/tree/main/Experimentation/Swarm-o-codex
