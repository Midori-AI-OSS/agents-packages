"""Custom stage example.

This example demonstrates how to extend the pipeline with custom stages.
It shows:
- Creating a custom stage by extending BaseStage
- Implementing custom logic
- Integrating the custom stage into the pipeline
- Adding custom configuration

This is useful for:
- Domain-specific reasoning steps
- Custom pre/post-processing
- Integration with specialized tools
- Experimentation with new techniques

Run this example:
    uv run python examples/custom_stage.py
"""

import asyncio

from midori_ai_agent_base import get_agent
from midori_ai_logger import MidoriAiLogger

from midori_ai_agents_demo import PipelineConfig
from midori_ai_agents_demo import PipelineRequest
from midori_ai_agents_demo import ReasoningPipeline
from midori_ai_agents_demo import StageType

from midori_ai_agents_demo.models import StageContext

from midori_ai_agents_demo.stages import BaseStage


class CustomValidationStage(BaseStage):
    """Custom stage that validates reasoning outputs.
    
    This demonstrates how to create a custom stage that:
    - Extends BaseStage
    - Implements domain-specific logic
    - Integrates with the pipeline
    """

    def __init__(self, enabled: bool = True, logger: MidoriAiLogger | None = None):
        """Initialize the custom validation stage."""
        super().__init__(enabled=enabled, logger=logger)

    @property
    def stage_type(self) -> StageType:
        """Return the stage type.
        
        Note: For custom stages, you might want to add new enum values
        or use a generic CUSTOM type. For this demo, we'll use PREPROCESSING.
        """
        return StageType.PREPROCESSING

    async def _execute(self, context: StageContext) -> str:
        """Execute custom validation logic.
        
        This is where you implement your custom stage logic.
        In this example, we validate that previous outputs meet certain criteria.
        """
        self._logger.info("Running custom validation stage")

        if not context.previous_results:
            return "No previous results to validate"

        validation_results = []

        for result in context.previous_results:
            if result.output:
                checks = self._validate_output(result.output)

                validation_results.append(f"Stage {result.stage_type.value}: {checks}")

        return "\n".join(validation_results)

    def _validate_output(self, output: str) -> str:
        """Validate an output against custom criteria.
        
        This is where you implement your domain-specific validation logic.
        """
        checks = []

        if len(output) < 50:
            checks.append("✗ Too short")
        else:
            checks.append("✓ Adequate length")

        if "?" in output or "!" in output:
            checks.append("✓ Contains expressive punctuation")
        else:
            checks.append("✗ Missing expressive punctuation")

        return ", ".join(checks)


async def main():
    """Run a custom stage example."""
    print("=" * 80)
    print("Custom Stage Example")
    print("=" * 80)
    print()
    print("This example demonstrates how to extend the pipeline with custom stages.")
    print()

    print("Creating agent...")

    agent = await get_agent(backend="langchain", model="gpt-4o-mini", api_key=None)

    print("✓ Agent created")
    print()

    print("Creating pipeline with standard configuration...")

    config = PipelineConfig(enable_preprocessing=True, enable_working_awareness=True, enable_compaction=False, enable_reranking=False, parallel_execution=False, enable_metrics=True)

    pipeline = ReasoningPipeline(agent=agent, config=config)

    print("✓ Pipeline created")
    print()

    print("Creating custom validation stage...")

    custom_stage = CustomValidationStage(enabled=True)

    print("✓ Custom stage created")
    print()

    print("Note: In this demo, we're showing how to create a custom stage.")
    print("In production, you would integrate it into the pipeline's stage list.")
    print()

    print("Processing request through standard pipeline...")

    request = PipelineRequest(prompt="What is the difference between machine learning and deep learning?")

    result = await pipeline.process(request)

    print("✓ Standard pipeline complete")
    print()

    print("Running custom validation stage on results...")

    from midori_ai_agents_demo.models import StageContext

    validation_context = StageContext(request=request, previous_results=result.stages)

    validation_result = await custom_stage.execute(validation_context)

    print()
    print("=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    print()
    print(validation_result.output)
    print()

    print("=" * 80)
    print("CUSTOM STAGE DEVELOPMENT TIPS")
    print("=" * 80)
    print()
    print("1. Extend BaseStage to get timing, error handling, and logging")
    print("2. Implement stage_type property (or add new enum values)")
    print("3. Implement _execute() with your custom logic")
    print("4. Use context.previous_results to access previous stage outputs")
    print("5. Use context.shared_data to share data between stages")
    print("6. Return a string output (or raise an exception on error)")
    print()
    print("To integrate into the pipeline:")
    print("  - Add your stage to the pipeline's stage list")
    print("  - Configure enable/disable in PipelineConfig")
    print("  - Add configuration options in config.py")
    print()

    print("Example complete!")


if __name__ == "__main__":
    asyncio.run(main())
