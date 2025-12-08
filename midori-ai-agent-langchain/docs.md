# midori-ai-agent-langchain Documentation

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
