# Agents Python Package Monorepo

[![Midori AI photo](https://tea-cup.midori-ai.xyz/download/logo_color1.png)](https://io.midori-ai.xyz/)

**Midori AI Agents** is a collection of Python packages for building LRM agents systems.

---

## Getting Started

### Installing All Packages

Install the complete suite of Midori AI agent packages with a single command using your preferred package manager:

**With UV (recommended):**

```bash
# Add to your Python project
uv add "git+https://github.com/Midori-AI-OSS/agents-packages.git#subdirectory=midori-ai-agents-all"

# Or install in a temporary environment
uv pip install "git+https://github.com/Midori-AI-OSS/agents-packages.git#subdirectory=midori-ai-agents-all"
```

**With Pip:**

```bash
pip install "git+https://github.com/Midori-AI-OSS/agents-packages.git#subdirectory=midori-ai-agents-all"
```

This installs all Midori AI packages along with embedded documentation that you can access programmatically.

---

## Package Documentation

Each package has detailed documentation in its `docs.md` file:

### Core Agent Packages

- [**midori-ai-agent-base**](./midori-ai-agent-base/docs.md) - Common protocol and data models for agent backends
- [**midori-ai-agent-context-manager**](./midori-ai-agent-context-manager/docs.md) - Context management and memory persistence
- [**midori-ai-agent-huggingface**](./midori-ai-agent-huggingface/docs.md) - HuggingFace local inference backend
- [**midori-ai-agent-langchain**](./midori-ai-agent-langchain/docs.md) - Langchain backend implementation
- [**midori-ai-agent-openai**](./midori-ai-agent-openai/docs.md) - OpenAI Agents SDK backend

### Intelligence & Processing

- [**midori-ai-compactor**](./midori-ai-compactor/docs.md) - Multi-model reasoning consolidation
- [**midori-ai-context-bridge**](./midori-ai-context-bridge/docs.md) - Persistent thinking cache with decay
- [**midori-ai-mood-engine**](./midori-ai-mood-engine/docs.md) - Comprehensive mood management system
- [**midori-ai-reranker**](./midori-ai-reranker/docs.md) - Document reranking and filtering
- [**midori-ai-vector-manager**](./midori-ai-vector-manager/docs.md) - Vector storage abstraction

### Media Management

- [**midori-ai-media-lifecycle**](./midori-ai-media-lifecycle/docs.md) - Time-based media decay and cleanup
- [**midori-ai-media-request**](./midori-ai-media-request/docs.md) - Type-safe media request/response interface
- [**midori-ai-media-vault**](./midori-ai-media-vault/docs.md) - Encrypted media storage

### Utilities & Examples

- [**midori-ai-agents-all**](./midori-ai-agents-all/docs.md) - Meta-package with all packages and embedded docs
- [**midori-ai-agents-demo**](./midori-ai-agents-demo/docs.md) - Example implementations and demos
