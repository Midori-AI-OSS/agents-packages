# midori-ai-compactor Documentation

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
