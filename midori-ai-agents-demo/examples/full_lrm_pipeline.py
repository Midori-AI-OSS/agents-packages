"""Full LRM pipeline example.

This example demonstrates a complete Large Reasoning Model pipeline
with all stages enabled and all Midori AI packages integrated. It shows:
- All stages working together
- Integration of agent-base, compactor, reranker, context-bridge, vector-manager
- Full observability with metrics and tracing
- Complex reasoning tasks

Run this example:
    uv run python examples/full_lrm_pipeline.py
"""

import asyncio

from midori_ai_agent_base import get_agent

from midori_ai_compactor import ThinkingCompactor

from midori_ai_reranker import RerankerPipeline

from midori_ai_agents_demo import PipelineConfig
from midori_ai_agents_demo import PipelineRequest
from midori_ai_agents_demo import ReasoningPipeline


async def main():
    """Run a full LRM pipeline example."""
    print("=" * 80)
    print("Full LRM Pipeline Example")
    print("=" * 80)
    print()
    print("This example demonstrates all Midori AI packages working together")
    print("in a complete reasoning pipeline.")
    print()

    print("Creating primary agent...")

    agent = await get_agent(backend="langchain", model="gpt-4o-mini", api_key=None)

    print("Agent created successfully")
    print()

    print("Creating compactor for output consolidation...")

    compactor = ThinkingCompactor(agent=agent)

    print("Compactor created successfully")
    print()

    print("Creating reranker for result prioritization...")

    reranker = RerankerPipeline()

    print("Reranker created successfully")
    print()

    print("Configuring full pipeline with all stages enabled...")

    config = PipelineConfig(enable_preprocessing=True, enable_working_awareness=True, enable_compaction=True, enable_reranking=True, parallel_execution=True, enable_metrics=True, enable_tracing=True, log_level="INFO")

    print("Creating pipeline with all integrations...")

    pipeline = ReasoningPipeline(agent=agent, config=config, compactor=compactor, reranker=reranker)

    print("Pipeline created successfully")
    print()

    print("Processing complex reasoning request...")
    print()

    request = PipelineRequest(prompt="Design a distributed caching system that can handle 1 million requests per second. Consider consistency, availability, partition tolerance, and cost.", context="The system should be deployable on AWS, handle data replication across multiple regions, and provide sub-millisecond latency.", constraints=["Must use open-source technologies", "Budget is $10,000/month", "Must handle graceful degradation"])

    print("Request details:")
    print(f"  Prompt: {request.prompt[:80]}...")
    print(f"  Context: {request.context[:80] if request.context else 'None'}...")
    print(f"  Constraints: {len(request.constraints) if request.constraints else 0}")
    print()

    result = await pipeline.process(request)

    print("=" * 80)
    print("FINAL RESULT")
    print("=" * 80)
    print()
    print(result.final_response)
    print()

    print("=" * 80)
    print("PIPELINE EXECUTION DETAILS")
    print("=" * 80)
    print()
    print(f"Total Duration: {result.total_duration_ms:.2f}ms")
    print(f"Cache Hits: {result.cache_hits}")
    print(f"Timestamp: {result.timestamp}")
    print()

    print("Stage Execution:")

    for i, stage in enumerate(result.stages, 1):
        print(f"\n{i}. {stage.stage_type.value.replace('_', ' ').title()}")
        print(f"   Status: {stage.status.value}")
        print(f"   Duration: {stage.duration_ms:.2f}ms")

        if stage.error:
            print(f"   Error: {stage.error}")

        if stage.output:
            output_preview = stage.output[:200] + "..." if len(stage.output) > 200 else stage.output

            print(f"   Output: {output_preview}")

    print()

    if "metrics" in result.metadata:
        print("=" * 80)
        print("PERFORMANCE METRICS")
        print("=" * 80)
        print()

        for metric, value in result.metadata["metrics"].items():
            print(f"  {metric}: {value:.2f}")

        print()

    if "trace_id" in result.metadata:
        print(f"Distributed Trace ID: {result.metadata['trace_id']}")
        print("(Use this ID to view the full trace in your tracing system)")
        print()

    print("=" * 80)
    print("PACKAGE INTEGRATIONS DEMONSTRATED")
    print("=" * 80)
    print()
    print("✓ midori-ai-agent-base    - Agent protocol and payload management")
    print("✓ midori-ai-agent-langchain - Langchain backend adapter")
    print("✓ midori-ai-compactor     - Multi-output consolidation")
    print("✓ midori-ai-reranker      - Result quality ranking")
    print("✓ midori_ai_logger        - Structured logging")
    print()
    print("This demo shows how all packages work together in a real LRM pipeline.")
    print()
    print("Example complete!")


if __name__ == "__main__":
    asyncio.run(main())
