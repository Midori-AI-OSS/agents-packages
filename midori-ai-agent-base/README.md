# midori-ai-agent-base

Common protocol and data models for Midori AI agent backends. Install directly from the repo using `git+`.

## Install from Git

### UV

Python Project Install
```bash
uv add "git+https://github.com/Midori-AI-OSS/agents-packages.git#subdirectory=midori-ai-agent-base"
```

Temp Venv Install
```bash
uv pip install "git+https://github.com/Midori-AI-OSS/agents-packages.git#subdirectory=midori-ai-agent-base"
```

### Pip

```bash
pip install "git+https://github.com/Midori-AI-OSS/agents-packages.git#subdirectory=midori-ai-agent-base"
```

## Response Parsing Helper

The `parse_structured_response` helper is provided to parse structured responses from different providers and separate reasoning from the final response:

```python
from midori_ai_agent_base import parse_structured_response

# Parse a structured response with reasoning and text blocks
content = [
    {"type": "reasoning", "content": [{"text": "I should be helpful."}]},
    {"type": "text", "text": "Hello! How can I help you?"}
]
thinking, response = parse_structured_response(content)
# thinking = "I should be helpful."
# response = "Hello! How can I help you?"

# Simple string responses work too
thinking, response = parse_structured_response("Just a simple response")
# thinking = ""
# response = "Just a simple response"
```

This helper is used internally by all adapter implementations to ensure consistent parsing of provider outputs.
