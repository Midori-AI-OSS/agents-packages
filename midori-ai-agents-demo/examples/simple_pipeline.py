"""Simple pipeline example.

This example demonstrates the most basic usage of the reasoning pipeline
with minimal configuration. It shows how to:
- Create a simple agent
- Configure a basic pipeline
- Process a single request
- Access the results

Run this example:
    uv run python examples/simple_pipeline.py
"""

import asyncio

from midori_ai_agent_base import get_agent

from midori_ai_agents_demo import PipelineConfig
from midori_ai_agents_demo import PipelineRequest
from midori_ai_agents_demo import ReasoningPipeline


async def main():
    """Run a simple pipeline example."""
    print("=" * 80)
    print("Simple Pipeline Example")
    print("=" * 80)
    print()

    print("Note: This example requires a valid API key for the backend you choose.")
    print("Set environment variables like OPENAI_API_KEY or ANTHROPIC_API_KEY")
    print()

    print("Creating agent...")

    agent = await get_agent(backend="langchain", model="gpt-4o-mini", api_key=None)

    print("Agent created successfully")
    print()

    print("Configuring pipeline with only essential stages...")

    config = PipelineConfig(enable_preprocessing=True, enable_working_awareness=False, enable_compaction=False, enable_reranking=False, parallel_execution=False, enable_metrics=True, enable_tracing=False)

    print("Creating pipeline...")

    pipeline = ReasoningPipeline(agent=agent, config=config)

    print("Pipeline created successfully")
    print()

    print("Processing request...")
    print()

    request = PipelineRequest(prompt="Explain the concept of recursion in programming in simple terms.")

    result = await pipeline.process(request)

    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()
    print(f"Final Response:\n{result.final_response}")
    print()
    print(f"Total Duration: {result.total_duration_ms:.2f}ms")
    print()
    print(f"Stages Executed: {len(result.stages)}")

    for stage in result.stages:
        print(f"  - {stage.stage_type.value}: {stage.status.value} ({stage.duration_ms:.2f}ms)")

    print()

    if "metrics" in result.metadata:
        print("Metrics Summary:")

        for metric, value in result.metadata["metrics"].items():
            print(f"  {metric}: {value:.2f}")

    print()
    print("Example complete!")


if __name__ == "__main__":
    asyncio.run(main())
