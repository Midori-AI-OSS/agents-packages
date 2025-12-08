# Reasoning Pipeline Demo Guide

**🚨 This is a DEMO/SHOWCASE Package 🚨**

This guide provides step-by-step scenarios demonstrating how to use the reasoning pipeline and integrate all Midori AI packages. Each scenario builds on the previous one, showing progressively more advanced features.

## Prerequisites

Before starting, ensure you have:

1. **Python 3.13+** installed
2. **uv** package manager: `curl -LsSf https://astral.sh/uv/install.sh | sh`
3. **API Keys** (for non-local examples):
   - OpenAI: `export OPENAI_API_KEY=your-key`
   - Anthropic: `export ANTHROPIC_API_KEY=your-key`
   - Or other supported backends

## Scenario 1: Hello World Pipeline

**Goal:** Run the simplest possible pipeline to understand basic concepts.

**Time:** 5 minutes

### Steps

1. **Install the package:**
```bash
cd Rest-Servers/packages/midori-ai-agents-demo
uv sync
```

2. **Run the simple example:**
```bash
uv run python examples/simple_pipeline.py
```

### What You'll See

- Pipeline initialization
- Single preprocessing stage execution
- Final response generation
- Timing metrics

### Key Concepts

- **PipelineRequest**: Wraps your input prompt
- **PipelineConfig**: Controls which stages run
- **PipelineResponse**: Contains results and metadata
- **Stages**: Independent processing steps

### Next Steps

Try modifying the prompt in `simple_pipeline.py` to see how the pipeline handles different inputs.

---

## Scenario 2: Enabling Multiple Stages

**Goal:** Enable multiple stages and observe how they work together.

**Time:** 10 minutes

### Steps

1. **Create a new script** `my_pipeline.py`:

```python
import asyncio
from midori_ai_agent_base import get_agent
from midori_ai_agents_demo import (
    PipelineConfig,
    PipelineRequest,
    ReasoningPipeline
)

async def main():
    # Create agent
    agent = await get_agent(backend="langchain", model="gpt-4o-mini")
    
    # Enable multiple stages
    config = PipelineConfig(
        enable_preprocessing=True,
        enable_working_awareness=True,  # NEW!
        enable_compaction=True,         # NEW!
        enable_reranking=False,
        enable_metrics=True,
    )
    
    # Create pipeline
    pipeline = ReasoningPipeline(agent=agent, config=config)
    
    # Process complex request
    request = PipelineRequest(
        prompt="Compare and contrast functional and object-oriented programming",
        constraints=["Be concise", "Use examples"]
    )
    
    result = await pipeline.process(request)
    
    # Print results
    print(f"Final Response:\n{result.final_response}\n")
    
    # Show stage breakdown
    print("Stage Breakdown:")
    for stage in result.stages:
        print(f"  {stage.stage_type.value}: {stage.duration_ms:.2f}ms")

if __name__ == "__main__":
    asyncio.run(main())
```

2. **Run your script:**
```bash
uv run python my_pipeline.py
```

### What You'll See

- **Preprocessing**: Validates and normalizes the input
- **Working Awareness**: Generates 3 different perspectives in parallel
- **Compaction**: Consolidates the perspectives into one coherent output
- **Final Response**: Synthesizes everything into the final answer

### Key Concepts

- **Working Awareness**: Demonstrates parallel execution with asyncio.gather
- **Compaction**: Uses midori-ai-compactor to deduplicate thinking
- **Stage Dependencies**: Some stages depend on previous outputs

### Experiment

Try disabling compaction (`enable_compaction=False`) and see how the output changes.

---

## Scenario 3: Full Pipeline with All Packages

**Goal:** Use all Midori AI packages together in a complete LRM pipeline.

**Time:** 15 minutes

### Steps

1. **Run the full pipeline example:**
```bash
uv run python examples/full_lrm_pipeline.py
```

### What You'll See

All stages running together:
1. **Preprocessing** (agent-base)
2. **Working Awareness** (parallel execution)
3. **Compaction** (midori-ai-compactor)
4. **Reranking** (midori-ai-reranker)
5. **Final Response** (synthesis)

Plus:
- Metrics collection
- Distributed tracing
- Comprehensive logging

### Key Concepts

- **Full Integration**: All packages working together
- **Reranking**: Prioritizes multiple candidates by quality
- **Observability**: Metrics and tracing throughout
- **Comprehensive Results**: Detailed stage-by-stage breakdown

### Experiment

1. Check the `metrics` in the result metadata
2. Look for the `trace_id` for distributed tracing
3. Compare execution times with and without parallel execution

---

## Scenario 4: 100% Local Inference

**Goal:** Run the entire pipeline locally without external APIs.

**Time:** 20 minutes (plus model download time)

### Prerequisites

Install additional dependencies:
```bash
uv pip install transformers torch accelerate
```

### Steps

1. **Run with a local model:**
```bash
python examples/local_setup.py --model gpt-oss-20b --device cpu
```

**Note:** First run will download the model (several GB). Use `--device cuda` if you have a GPU.

### What You'll See

- Local model initialization
- Slower inference (no cloud acceleration)
- Complete privacy (nothing leaves your machine)
- No API costs

### Key Concepts

- **midori-ai-agent-huggingface**: Adapter for local HuggingFace models
- **Local Inference**: Trade-off between cost/privacy vs speed
- **Device Selection**: CPU vs GPU inference

### Experiment

Try different models:
- `gpt-oss-20b` (smaller, faster)
- Other open-source models available on HuggingFace

---

## Scenario 5: Custom Stages

**Goal:** Extend the pipeline with your own custom processing stage.

**Time:** 25 minutes

### Steps

1. **Study the custom stage example:**
```bash
uv run python examples/custom_stage.py
```

2. **Create your own custom stage:**

```python
from midori_ai_agents_demo.stages import BaseStage
from midori_ai_agents_demo import StageType
from midori_ai_agents_demo.models import StageContext

class SentimentAnalysisStage(BaseStage):
    """Custom stage that analyzes sentiment of reasoning output."""
    
    @property
    def stage_type(self) -> StageType:
        return StageType.PREPROCESSING  # Reuse existing enum
    
    async def _execute(self, context: StageContext) -> str:
        # Your custom logic here
        outputs = [r.output for r in context.previous_results if r.output]
        
        # Simple sentiment analysis (in production, use a proper model)
        positive_words = ["good", "great", "excellent", "positive"]
        negative_words = ["bad", "poor", "negative", "wrong"]
        
        sentiment_scores = []
        for output in outputs:
            pos_count = sum(1 for word in positive_words if word in output.lower())
            neg_count = sum(1 for word in negative_words if word in output.lower())
            sentiment_scores.append(f"Positive: {pos_count}, Negative: {neg_count}")
        
        return "Sentiment Analysis:\n" + "\n".join(sentiment_scores)
```

3. **Integrate your custom stage:**

```python
# Create your custom stage
sentiment_stage = SentimentAnalysisStage(enabled=True)

# Run it after other stages
result = await pipeline.process(request)
sentiment_result = await sentiment_stage.execute(
    StageContext(request=request, previous_results=result.stages)
)

print(f"Custom Analysis:\n{sentiment_result.output}")
```

### Key Concepts

- **BaseStage**: Provides timing, error handling, logging
- **stage_type**: Identifies your stage
- **_execute()**: Your custom logic
- **StageContext**: Access to request and previous results

### Experiment

Create custom stages for:
- Domain-specific validation
- Custom formatting
- Integration with external tools
- Specialized reasoning techniques

---

## Scenario 6: Observability Deep Dive

**Goal:** Explore metrics, tracing, and logging capabilities.

**Time:** 15 minutes

### Steps

1. **Enable full observability:**

```python
config = PipelineConfig(
    enable_preprocessing=True,
    enable_working_awareness=True,
    enable_compaction=True,
    enable_metrics=True,    # Enable metrics
    enable_tracing=True,    # Enable tracing
    log_level="DEBUG",      # Verbose logging
)
```

2. **Run and analyze:**

```python
result = await pipeline.process(request)

# Metrics
print("Metrics:")
for metric, value in result.metadata["metrics"].items():
    print(f"  {metric}: {value:.2f}")

# Tracing
trace_id = result.metadata.get("trace_id")
print(f"\nTrace ID: {trace_id}")
print("(Use this to view the trace in your tracing system)")

# Stage timing
print("\nStage Timing:")
for stage in result.stages:
    print(f"  {stage.stage_type.value:20s} {stage.duration_ms:8.2f}ms")
```

### What You'll See

- **Metrics**: Average, min, max durations per stage
- **Trace ID**: For distributed tracing systems
- **Detailed Logs**: Every operation logged
- **Stage Breakdown**: Timing for each stage

### Key Concepts

- **MetricsCollector**: Collects timing and performance data
- **Tracer**: Creates hierarchical trace spans
- **midori_ai_logger**: Structured logging throughout

### Experiment

1. Compare metrics across different prompts
2. Identify bottleneck stages
3. Optimize configuration based on metrics

---

## Scenario 7: Configuration Patterns

**Goal:** Master configuration for different use cases.

**Time:** 10 minutes

### Configuration Profiles

#### 1. Development Profile
Fast iteration, full observability:
```python
config = PipelineConfig(
    enable_preprocessing=True,
    enable_working_awareness=False,  # Skip for speed
    enable_compaction=False,         # Skip for speed
    enable_reranking=False,          # Skip for speed
    parallel_execution=True,
    cache_strategy="none",           # No caching in dev
    enable_metrics=True,
    enable_tracing=True,
    log_level="DEBUG",
)
```

#### 2. Production Profile
All stages, optimized caching:
```python
config = PipelineConfig(
    enable_preprocessing=True,
    enable_working_awareness=True,
    enable_compaction=True,
    enable_reranking=True,
    parallel_execution=True,
    cache_strategy="memory",         # Fast caching
    cache_ttl_seconds=3600,
    enable_metrics=True,
    enable_tracing=True,             # For debugging
    log_level="INFO",                # Less verbose
    max_retries=3,
    timeout_seconds=60.0,
)
```

#### 3. Cost-Optimized Profile
Fewer agent calls, more caching:
```python
config = PipelineConfig(
    enable_preprocessing=True,
    enable_working_awareness=False,  # Saves API calls
    enable_compaction=False,         # Saves API calls
    enable_reranking=False,
    cache_strategy="memory",
    cache_ttl_seconds=7200,          # Longer cache
    enable_metrics=False,            # Save resources
    enable_tracing=False,
    log_level="WARNING",
)
```

### Key Concepts

- Different use cases need different configurations
- Trade-offs between speed, cost, and quality
- Cache strategies impact both performance and cost
- Observability has a (small) performance cost

---

## Scenario 8: Error Handling

**Goal:** Understand how the pipeline handles errors.

**Time:** 10 minutes

### Steps

1. **Test with invalid input:**

```python
# Trigger an error by using an invalid backend
try:
    agent = await get_agent(backend="invalid-backend")
except Exception as e:
    print(f"Error creating agent: {e}")

# Or test error handling in the pipeline
result = await pipeline.process("")  # Empty prompt

# Check for errors
for stage in result.stages:
    if stage.error:
        print(f"Stage {stage.stage_type.value} failed: {stage.error}")
```

### What You'll See

- Graceful error handling
- Error messages in stage results
- Pipeline continues when possible
- Failed stages marked with status="failed"

### Key Concepts

- **Resilience**: Stages fail independently
- **Error Propagation**: Errors reported but don't crash the pipeline
- **Status Tracking**: Each stage has a status (pending, running, completed, failed, skipped)

---

## Advanced Topics

### A. Parallel Stage Execution

The pipeline automatically runs independent stages in parallel:

```python
config = PipelineConfig(parallel_execution=True)
```

Stages that don't depend on each other run concurrently using `asyncio.gather`.

### B. Custom Caching

Implement your own cache (Redis, Memcached, etc.):

```python
from midori_ai_agents_demo.caching import CacheProtocol

class RedisCache(CacheProtocol):
    async def get(self, key: str):
        # Your Redis implementation
        pass
    
    async def set(self, key: str, value: str, ttl_seconds: int):
        # Your Redis implementation
        pass
    
    # ... implement other methods

cache = RedisCache()
pipeline = ReasoningPipeline(agent=agent, cache=cache)
```

### C. Multiple Agents

Use different agents for different stages:

```python
# Fast agent for preprocessing
fast_agent = await get_agent(backend="langchain", model="gpt-4o-mini")

# Powerful agent for main reasoning
powerful_agent = await get_agent(backend="langchain", model="gpt-4")

# Create stages with different agents
preprocessing = PreprocessingStage(agent=fast_agent)
working_awareness = WorkingAwarenessStage(agent=powerful_agent)
```

## Troubleshooting

### Issue: Tests failing with import errors

**Solution:** Make sure you're in the package directory and have synced dependencies:
```bash
cd Rest-Servers/packages/midori-ai-agents-demo
uv sync
```

### Issue: API rate limits

**Solution:** Enable caching and reduce parallel perspectives:
```python
config = PipelineConfig(
    cache_strategy="memory",
    cache_ttl_seconds=3600,
    enable_working_awareness=False,  # Reduces API calls
)
```

### Issue: Slow local inference

**Solution:** Use GPU and smaller models:
```bash
python examples/local_setup.py --model gpt-oss-20b --device cuda
```

### Issue: Out of memory

**Solution:** Reduce max_tokens and disable working_awareness:
```python
config = PipelineConfig(
    enable_working_awareness=False,
    max_tokens=500,
)
```

## Next Steps

1. **Experiment**: Modify the examples to suit your needs
2. **Extend**: Create custom stages for your domain
3. **Integrate**: Use in your own applications
4. **Adapt**: Take these patterns to production with proper testing

## Remember

This is a **demo package** designed for:
- ✅ Learning and experimentation
- ✅ Integration reference
- ✅ Prototyping

For production use:
- Add comprehensive testing
- Implement proper error handling
- Add monitoring and alerts
- Harden security
- Optimize performance

---

**Have fun exploring the Midori AI reasoning pipeline!** 🚀
