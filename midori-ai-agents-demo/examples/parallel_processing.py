"""Parallel processing example.

This example demonstrates how the pipeline executes multiple stages
in parallel when possible. It shows:
- Enabling multiple independent stages
- Parallel execution with asyncio.gather
- Performance benefits of parallelism
- Timing breakdown by stage

Run this example:
    uv run python examples/parallel_processing.py
"""

import asyncio

from midori_ai_agent_base import get_agent

from midori_ai_agents_demo import PipelineConfig
from midori_ai_agents_demo import PipelineRequest
from midori_ai_agents_demo import ReasoningPipeline


async def main():
    """Run a parallel processing example."""
    print("=" * 80)
    print("Parallel Processing Example")
    print("=" * 80)
    print()

    print("This example demonstrates parallel stage execution in the reasoning pipeline.")
    print()

    print("Creating agent...")

    agent = await get_agent(backend="langchain", model="gpt-4o-mini", api_key=None)

    print("Agent created successfully")
    print()

    print("Configuring pipeline with parallel execution enabled...")

    config = PipelineConfig(enable_preprocessing=True, enable_working_awareness=True, enable_compaction=True, enable_reranking=False, parallel_execution=True, enable_metrics=True, enable_tracing=True)

    print("Creating pipeline...")

    pipeline = ReasoningPipeline(agent=agent, config=config)

    print("Pipeline created successfully")
    print()

    print("Processing request with parallel stage execution...")
    print()

    request = PipelineRequest(prompt="What are the trade-offs between different sorting algorithms?", context="Focus on time complexity, space complexity, and practical use cases.")

    result = await pipeline.process(request)

    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()
    print(f"Final Response:\n{result.final_response}")
    print()
    print("=" * 80)
    print("PERFORMANCE METRICS")
    print("=" * 80)
    print()
    print(f"Total Duration: {result.total_duration_ms:.2f}ms")
    print()
    print("Stage Breakdown:")

    for stage in result.stages:
        status_symbol = "✓" if stage.status.value == "completed" else "✗"

        print(f"  {status_symbol} {stage.stage_type.value:20s} {stage.status.value:10s} {stage.duration_ms:8.2f}ms")

    print()

    if "metrics" in result.metadata:
        print("Aggregate Metrics:")

        for metric, value in result.metadata["metrics"].items():
            print(f"  {metric}: {value:.2f}")

    print()

    if "trace_id" in result.metadata:
        print(f"Trace ID: {result.metadata['trace_id']}")
        print("(In production, this would link to your distributed tracing system)")

    print()
    print("Example complete!")
    print()
    print("Note: The working_awareness stage runs multiple perspectives in parallel,")
    print("demonstrating how asyncio.gather enables concurrent execution.")


if __name__ == "__main__":
    asyncio.run(main())
