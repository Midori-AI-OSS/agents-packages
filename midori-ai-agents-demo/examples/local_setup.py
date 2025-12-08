"""Local setup example with 100% local inference.

This example demonstrates how to run the entire pipeline locally
without any external API dependencies. It uses:
- midori-ai-agent-huggingface for local model inference
- Local embedding models
- No cloud API keys required

This is perfect for:
- Development and testing
- Privacy-sensitive applications
- Offline scenarios
- Cost-conscious deployments

Run this example:
    python examples/local_setup.py --model gpt-oss-20b

Requirements:
- Sufficient RAM (16GB+ recommended)
- GPU optional but recommended
- Local model files downloaded
"""

import argparse
import asyncio

from midori_ai_agent_base import get_agent

from midori_ai_compactor import ThinkingCompactor

from midori_ai_reranker import RerankerPipeline

from midori_ai_agents_demo import PipelineConfig
from midori_ai_agents_demo import PipelineRequest
from midori_ai_agents_demo import ReasoningPipeline


async def main():
    """Run a fully local pipeline example."""
    parser = argparse.ArgumentParser(description="Run reasoning pipeline with local inference")

    parser.add_argument("--model", type=str, default="gpt-oss-20b", help="Local model to use (default: gpt-oss-20b)")

    parser.add_argument("--device", type=str, default="auto", help="Device to run on (cpu, cuda, auto)")

    parser.add_argument("--max-tokens", type=int, default=500, help="Maximum tokens to generate")

    args = parser.parse_args()

    print("=" * 80)
    print("100% Local Setup Example")
    print("=" * 80)
    print()
    print("This example runs the entire pipeline locally without external APIs.")
    print()

    print("Configuration:")
    print(f"  Model: {args.model}")
    print(f"  Device: {args.device}")
    print(f"  Max Tokens: {args.max_tokens}")
    print()

    print("Creating local agent with Hugging Face backend...")

    try:
        agent = await get_agent(backend="huggingface", model=args.model, device=args.device, max_tokens=args.max_tokens)

        print("✓ Local agent created successfully")
    except Exception as e:
        print(f"✗ Failed to create local agent: {e}")
        print()
        print("Make sure you have:")
        print("  1. Installed transformers and torch: pip install transformers torch")
        print("  2. Downloaded the model files")
        print("  3. Sufficient RAM/VRAM")

        return

    print()

    print("Creating compactor (also using local agent)...")

    compactor = ThinkingCompactor(agent=agent)

    print("✓ Compactor created")
    print()

    print("Creating reranker (using local models)...")

    reranker = RerankerPipeline()

    print("✓ Reranker created")
    print()

    print("Configuring pipeline...")

    config = PipelineConfig(enable_preprocessing=True, enable_working_awareness=True, enable_compaction=True, enable_reranking=True, parallel_execution=True, enable_metrics=True, log_level="INFO")

    print("Creating fully local pipeline...")

    pipeline = ReasoningPipeline(agent=agent, config=config, compactor=compactor, reranker=reranker)

    print("✓ Pipeline created")
    print()

    print("Processing request locally...")
    print()

    request = PipelineRequest(prompt="Explain how neural networks learn through backpropagation. Keep it simple but accurate.")

    print(f"Request: {request.prompt}")
    print()
    print("Processing (this may take a while with local inference)...")
    print()

    result = await pipeline.process(request)

    print("=" * 80)
    print("RESULT")
    print("=" * 80)
    print()
    print(result.final_response)
    print()

    print("=" * 80)
    print("PERFORMANCE")
    print("=" * 80)
    print()
    print(f"Total Duration: {result.total_duration_ms:.2f}ms ({result.total_duration_ms / 1000:.2f}s)")
    print()

    print("Stage Timing:")

    for stage in result.stages:
        print(f"  {stage.stage_type.value:20s} {stage.duration_ms:8.2f}ms")

    print()

    print("=" * 80)
    print("LOCAL INFERENCE ADVANTAGES")
    print("=" * 80)
    print()
    print("✓ No API keys required")
    print("✓ No external network dependencies")
    print("✓ Complete privacy (data never leaves your machine)")
    print("✓ Predictable costs (no per-token charges)")
    print("✓ Full control over model and parameters")
    print()
    print("Trade-offs:")
    print("  - Slower inference (no optimized cloud infrastructure)")
    print("  - Requires local compute resources (RAM/GPU)")
    print("  - Limited to open-source models")
    print()

    print("Example complete!")


if __name__ == "__main__":
    asyncio.run(main())
