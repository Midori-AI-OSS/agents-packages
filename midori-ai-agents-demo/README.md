# midori-ai-agents-demo

**🚨 This is a DEMO/SHOWCASE Package 🚨**

This package demonstrates how to build a complete Large Reasoning Model (LRM) pipeline by integrating all Midori AI packages. It serves as an **educational reference** and **integration blueprint**, not as production-ready code.

## Purpose

This demo showcases:
- **Package Integration**: How to combine agent-base, agent-langchain, agent-openai, agent-huggingface, context-bridge, compactor, vector-manager, and reranker
- **Modular Architecture**: Independent stages that can be studied and adapted separately
- **Best Practices**: Async patterns, error handling, caching strategies, and observability
- **Configuration**: Building flexible, configurable reasoning systems
- **Local Inference**: 100% local setup examples using Hugging Face models

## What This Is NOT
 
❌ Performance-optimized for critical workloads  
❌ Hardened for mission-critical systems  

## Install from Git

### UV

Python Project Install
```bash
uv add "git+https://github.com/Midori-AI-OSS/agents-packages.git#subdirectory=midori-ai-agents-demo"
```

Temp Venv Install
```bash
uv pip install "git+https://github.com/Midori-AI-OSS/agents-packages.git#subdirectory=midori-ai-agents-demo"
```

### Pip

```bash
pip install "git+https://github.com/Midori-AI-OSS/agents-packages.git#subdirectory=midori-ai-agents-demo"
```

## Quick Start

```python
from midori_ai_agents_demo import ReasoningPipeline, PipelineConfig
from midori_ai_agent_base import get_agent

# Create an agent for the pipeline
agent = await get_agent(
    backend="langchain",
    model="your-model",
    api_key="your-key",
)

# Configure the pipeline
config = PipelineConfig(
    enable_preprocessing=True,
    enable_working_awareness=True,
    enable_compaction=True,
    enable_reranking=True,
    parallel_execution=True,
)

# Create and run pipeline
pipeline = ReasoningPipeline(agent=agent, config=config)
result = await pipeline.process("Your reasoning task here")

print(result.final_response)
```

## Examples

See the `examples/` directory for comprehensive demos:
- `simple_pipeline.py` - Basic single-stage pipeline
- `parallel_processing.py` - Multi-stage parallel execution
- `full_lrm_pipeline.py` - Complete LRM demo with all packages
- `local_setup.py` - 100% local inference with Hugging Face
- `custom_stage.py` - Extending with custom stages

## Documentation

- **Quick Start**: This README
- **Detailed Guide**: See `docs.md` for comprehensive integration documentation
- **Step-by-Step Demos**: See `DEMO_GUIDE.md` for hands-on scenarios
- **API Reference**: Inline docstrings in all modules

## Use Cases

✅ Learning the Midori AI package ecosystem  
✅ Reference for building custom LRM pipelines  
✅ Experimentation with different package combinations  
✅ Prototyping new reasoning approaches  

## Contributing

This is a demo package. For production implementations, adapt these patterns to your specific needs with proper testing and hardening.

See `docs.md` for detailed documentation and usage examples.
