# midori-ai-agents-demo Documentation

**🚨 This is a DEMO/SHOWCASE Package 🚨**

This documentation provides a comprehensive guide to the reasoning pipeline demo package, showing how to integrate all Midori AI packages into a complete LRM (Large Reasoning Model) system.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Package Integrations](#package-integrations)
4. [Configuration](#configuration)
5. [Stages](#stages)
6. [Observability](#observability)
7. [Caching](#caching)
8. [Examples](#examples)
9. [Best Practices](#best-practices)
10. [Production Considerations](#production-considerations)

## Overview

The reasoning pipeline is a **demonstration package** that shows how to build a modular, observable, and configurable LRM system by integrating:

- **midori-ai-agent-base**: Agent protocol and payload management
- **midori-ai-agent-langchain**: Langchain backend adapter
- **midori-ai-agent-openai**: OpenAI backend adapter
- **midori-ai-agent-huggingface**: Local inference adapter
- **midori-ai-compactor**: Multi-output consolidation
- **midori-ai-reranker**: Result quality ranking
- **midori-ai-vector-manager**: Vector storage (via context-bridge)
- **midori-ai-context-bridge**: Context caching and grounding
- **midori_ai_logger**: Structured logging

### What This Package Is

✅ Educational reference for the Midori AI ecosystem  
✅ Integration blueprint for building LRM pipelines  
✅ Best practices demonstration  
✅ Prototyping and experimentation platform  

### What This Package Is NOT

❌ Production-ready code for critical systems  
❌ Replacement for existing production code  
❌ Optimized for performance-critical workloads  
❌ Hardened for mission-critical applications  

## Architecture

The pipeline follows a modular stage-based architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Reasoning Pipeline                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐                                         │
│  │ Preprocessing   │ ← Validates and normalizes input        │
│  └────────┬────────┘                                         │
│           │                                                   │
│  ┌────────▼─────────────┐                                    │
│  │ Working Awareness    │ ← Generates multiple perspectives  │
│  │ (Parallel Execution) │   in parallel                      │
│  └────────┬─────────────┘                                    │
│           │                                                   │
│  ┌────────▼────────┐                                         │
│  │ Compaction      │ ← Consolidates outputs                  │
│  └────────┬────────┘                                         │
│           │                                                   │
│  ┌────────▼────────┐                                         │
│  │ Reranking       │ ← Prioritizes results                   │
│  └────────┬────────┘                                         │
│           │                                                   │
│  ┌────────▼────────┐                                         │
│  │ Final Response  │ ← Synthesizes final answer              │
│  └─────────────────┘                                         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Modularity**: Each stage is independent and can be enabled/disabled
2. **Composability**: Stages can be added, removed, or reordered
3. **Observability**: Comprehensive metrics, logging, and tracing
4. **Flexibility**: Configuration-driven behavior
5. **Async-First**: Built on asyncio for performance

## Package Integrations

### midori-ai-agent-base

The agent-base package provides the protocol and data models for agent backends.

**Used in:**
- All stages that need to call agents
- Request/response handling
- Payload construction

**Example:**
```python
from midori_ai_agent_base import get_agent, AgentPayload

agent = await get_agent(backend="langchain", model="gpt-4")
payload = AgentPayload(prompt="Your prompt", max_tokens=500)
response = await agent.execute_with_reasoning(payload)
```

### midori-ai-compactor

The compactor consolidates multiple reasoning outputs into a single coherent message.

**Used in:**
- Compaction stage
- Deduplicating redundant thinking
- Synthesizing multiple perspectives

**Example:**
```python
from midori_ai_compactor import ThinkingCompactor

compactor = ThinkingCompactor(agent=agent)
outputs = ["Output 1", "Output 2", "Output 3"]
consolidated = await compactor.compact(outputs)
```

### midori-ai-reranker

The reranker prioritizes and ranks results by quality or relevance.

**Used in:**
- Reranking stage
- Quality assessment
- Result filtering

**Example:**
```python
from midori_ai_reranker import RerankerPipeline

reranker = RerankerPipeline()
ranked = await reranker.rerank(query="question", documents=candidates)
```

### midori_ai_logger

Structured logging across all components.

**Used in:**
- All stages
- Pipeline orchestrator
- Error reporting

**Example:**
```python
from midori_ai_logger import MidoriAILogger

logger = MidoriAILogger()
logger.info("Processing started")
logger.error("Error occurred", extra={"detail": "..."})
```

## Configuration

The pipeline is highly configurable via the `PipelineConfig` class:

```python
from midori_ai_agents_demo import PipelineConfig

config = PipelineConfig(
    # Stage toggles
    enable_preprocessing=True,
    enable_working_awareness=True,
    enable_compaction=True,
    enable_reranking=True,
    
    # Execution
    parallel_execution=True,
    max_retries=3,
    timeout_seconds=60.0,
    
    # Caching
    cache_strategy="memory",  # none, memory, persistent, vector
    cache_ttl_seconds=3600,
    
    # Integration
    vector_collection="reasoning_context",
    compactor_prompt=None,  # Use default
    reranker_model="cross-encoder",
    
    # Observability
    enable_metrics=True,
    enable_tracing=True,
    log_level="INFO",
)
```

### Configuration from TOML

You can also load configuration from a `config.toml` file:

```toml
[midori_ai_agents_demo]
enable_preprocessing = true
enable_working_awareness = true
parallel_execution = true
cache_strategy = "vector"
log_level = "DEBUG"
```

```python
from midori_ai_agents_demo import load_pipeline_config

config = load_pipeline_config()
```

## Stages

### Preprocessing Stage

**Purpose:** Validates and normalizes input for downstream processing.

**Demonstrates:**
- Using the agent-base protocol
- Building structured prompts
- Input validation patterns

**Configuration:**
- `enable_preprocessing`: Enable/disable this stage

**Output:** Normalized and validated input text

### Working Awareness Stage

**Purpose:** Generates multiple reasoning perspectives in parallel.

**Demonstrates:**
- Parallel execution with asyncio.gather
- Multiple concurrent agent calls
- Aggregating parallel results

**Configuration:**
- `enable_working_awareness`: Enable/disable this stage
- `num_perspectives`: Number of perspectives (default: 3)

**Output:** Combined reasoning from multiple perspectives

### Compaction Stage

**Purpose:** Consolidates multiple outputs using the compactor package.

**Demonstrates:**
- Integration with midori-ai-compactor
- Deduplication of redundant thinking
- Output synthesis

**Configuration:**
- `enable_compaction`: Enable/disable this stage
- `compactor_prompt`: Custom consolidation prompt

**Output:** Compacted and deduplicated reasoning

### Reranking Stage

**Purpose:** Prioritizes results by quality using the reranker package.

**Demonstrates:**
- Integration with midori-ai-reranker
- Quality assessment
- Result filtering

**Configuration:**
- `enable_reranking`: Enable/disable this stage
- `reranker_model`: Model to use for reranking

**Output:** Top-ranked result

### Final Response Stage

**Purpose:** Synthesizes all stage results into a coherent final answer.

**Demonstrates:**
- Gathering outputs from all stages
- Response synthesis
- Context and metadata inclusion

**Output:** Final user-facing response

## Observability

### Metrics

The pipeline collects comprehensive metrics when enabled:

```python
config = PipelineConfig(enable_metrics=True)
pipeline = ReasoningPipeline(agent=agent, config=config)

result = await pipeline.process("Your prompt")

# Access metrics
metrics = result.metadata["metrics"]
print(f"Avg preprocessing time: {metrics['preprocessing_avg_ms']}ms")
```

**Collected Metrics:**
- Stage duration (avg, min, max)
- Cache hits/misses
- Error counts
- Custom stage metrics

### Distributed Tracing

Enable tracing to track requests across stages:

```python
config = PipelineConfig(enable_tracing=True)
pipeline = ReasoningPipeline(agent=agent, config=config)

result = await pipeline.process("Your prompt")

# Access trace ID
trace_id = result.metadata["trace_id"]
print(f"Trace ID: {trace_id}")
```

### Logging

All stages log their operations using midori_ai_logger:

```python
config = PipelineConfig(log_level="DEBUG")  # INFO, DEBUG, WARNING, ERROR
```

## Caching

The pipeline supports multiple caching strategies:

### Memory Cache (Default)

Fast in-memory cache, lost on restart:

```python
config = PipelineConfig(cache_strategy="memory", cache_ttl_seconds=3600)
```

### No Cache

Disable caching entirely:

```python
config = PipelineConfig(cache_strategy="none")
```

### Custom Cache

Provide your own cache implementation:

```python
from midori_ai_agents_demo.caching import CacheProtocol

class MyCustomCache(CacheProtocol):
    # Implement cache methods
    pass

cache = MyCustomCache()
pipeline = ReasoningPipeline(agent=agent, cache=cache)
```

## Examples

The `examples/` directory contains comprehensive demos:

### Simple Pipeline
```bash
uv run python examples/simple_pipeline.py
```

Shows basic usage with minimal configuration.

### Parallel Processing
```bash
uv run python examples/parallel_processing.py
```

Demonstrates parallel stage execution and performance benefits.

### Full LRM Pipeline
```bash
uv run python examples/full_lrm_pipeline.py
```

Complete demo with all packages integrated.

### Local Setup
```bash
python examples/local_setup.py --model gpt-oss-20b
```

100% local inference using Hugging Face models.

### Custom Stage
```bash
uv run python examples/custom_stage.py
```

Shows how to extend the pipeline with custom stages.

## Best Practices

### 1. Configuration Management

Store configuration in `config.toml` rather than hardcoding:

```toml
[midori_ai_agents_demo]
enable_preprocessing = true
parallel_execution = true
log_level = "INFO"
```

### 2. Error Handling

Stages handle errors gracefully and report them in results:

```python
result = await pipeline.process(request)

for stage in result.stages:
    if stage.error:
        print(f"Stage {stage.stage_type} failed: {stage.error}")
```

### 3. Observability

Always enable metrics and tracing in production:

```python
config = PipelineConfig(
    enable_metrics=True,
    enable_tracing=True,
    log_level="INFO",
)
```

### 4. Caching Strategy

Choose the right cache for your use case:
- **Development/Testing**: `cache_strategy="none"`
- **Production (single instance)**: `cache_strategy="memory"`
- **Production (distributed)**: Use Redis or context-bridge
- **Semantic caching**: `cache_strategy="vector"`

### 5. Performance Tuning

Enable parallel execution and adjust stage configuration:

```python
config = PipelineConfig(
    parallel_execution=True,
    timeout_seconds=30.0,
    max_retries=2,
)
```

## Production Considerations

This is a **demo package**. Before using in production:

### 1. Testing

- Add comprehensive unit and integration tests
- Test edge cases and error scenarios
- Load test with realistic traffic
- Test failure modes and recovery

### 2. Security

- Validate all inputs
- Sanitize outputs
- Implement rate limiting
- Add authentication/authorization
- Review and harden error messages

### 3. Performance

- Profile and optimize hot paths
- Implement proper caching
- Add connection pooling
- Optimize agent calls
- Consider batch processing

### 4. Monitoring

- Integrate with Prometheus/Grafana
- Add alerts for errors and latency
- Monitor resource usage
- Track cache hit rates
- Set up distributed tracing

### 5. Reliability

- Implement circuit breakers
- Add retry with exponential backoff
- Handle timeouts gracefully
- Implement graceful degradation
- Add health checks

### 6. Scalability

- Use message queues for async processing
- Implement horizontal scaling
- Add load balancing
- Consider serverless deployment
- Optimize resource allocation

## Further Reading

- **Agent Base Docs**: See `midori-ai-agent-base/docs.md`
- **Compactor Docs**: See `midori-ai-compactor/docs.md`
- **Reranker Docs**: See `midori-ai-reranker/docs.md`
- **Vector Manager Docs**: See `midori-ai-vector-manager/docs.md`
- **Context Bridge Docs**: See `midori-ai-context-bridge/docs.md`

## Support

This is a demo package. For production support:
- Review existing Midori AI packages
- Adapt patterns to your needs
- Add proper testing and hardening
- Consult with your team

---

**Remember:** This package demonstrates integration patterns. Production implementations should be adapted to specific requirements with proper testing, monitoring, and hardening.
