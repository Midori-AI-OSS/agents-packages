# midori-ai-context-bridge

Persistent thinking cache with time-based memory decay. Uses `midori-ai-vector-manager` for vector storage. Install directly from the repo using `git+`.

## Architecture

- **Vector Storage**: Delegates to `midori-ai-vector-manager` (ChromaDB backend)
- **Decay/Corruption Logic**: Maintained in context-bridge
- **ReasoningEntry**: Wraps `VectorEntry` objects from vector-manager

## Install from Git

### UV

Python Project Install
```bash
uv add "git+https://github.com/Midori-AI-OSS/Carly-AGI#subdirectory=Rest-Servers/packages/midori-ai-context-bridge"
```

Temp Venv Install
```bash
uv pip install "git+https://github.com/Midori-AI-OSS/Carly-AGI#subdirectory=Rest-Servers/packages/midori-ai-context-bridge"
```

### Pip

```bash
pip install "git+https://github.com/Midori-AI-OSS/Carly-AGI#subdirectory=Rest-Servers/packages/midori-ai-context-bridge"
```

## Quick Start

```python
from midori_ai_context_bridge import ContextBridge, ModelType

bridge = ContextBridge(max_tokens_per_summary=500)

# Store reasoning
await bridge.store_reasoning(
    session_id="user:123",
    text="reasoning output...",
    model_type=ModelType.PREPROCESSING
)

# Get prior reasoning (with time-based decay)
context = await bridge.get_prior_reasoning(
    session_id="user:123",
    model_type=ModelType.PREPROCESSING
)
```

See `docs.md` for detailed documentation.
