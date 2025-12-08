# midori-ai-compactor

Flexible consolidation of multi-model reasoning outputs using agents. Install directly from the repo using `git+`.

## Install from Git

### UV

Python Project Install
```bash
uv add "git+https://github.com/Midori-AI-OSS/Carly-AGI#subdirectory=Rest-Servers/packages/midori-ai-compactor"
```

Temp Venv Install
```bash
uv pip install "git+https://github.com/Midori-AI-OSS/Carly-AGI#subdirectory=Rest-Servers/packages/midori-ai-compactor"
```

### Pip

```bash
pip install "git+https://github.com/Midori-AI-OSS/Carly-AGI#subdirectory=Rest-Servers/packages/midori-ai-compactor"
```

## Quick Start

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

# Consolidate multiple model outputs into a single message
outputs = ["Analysis from model 1", "Analysis from model 2"]
consolidated = await compactor.compact(outputs)
```

See `docs.md` for detailed documentation and usage examples.
