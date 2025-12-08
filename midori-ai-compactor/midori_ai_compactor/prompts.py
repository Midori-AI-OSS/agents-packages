"""Consolidation prompt templates for the compactor."""


DEFAULT_CONSOLIDATION_PROMPT = """You are an intelligent consolidation agent. Your task is to merge multiple reasoning outputs into a single, coherent, and easy-to-parse message.

INSTRUCTIONS:
1. Read all provided reasoning outputs carefully
2. Identify common themes, insights, and conclusions across all outputs
3. Resolve any contradictions by considering context and confidence levels
4. Produce a single consolidated output that captures the essential information
5. The output should be well-structured and easy to parse
6. Preserve important details from all sources
7. If outputs are in different languages, consolidate into the most common language or maintain multilingual structure if appropriate

REASONING OUTPUTS TO CONSOLIDATE:
{outputs}

CONSOLIDATED OUTPUT:"""


def format_outputs_for_prompt(outputs: list[str]) -> str:
    """Format a list of outputs for inclusion in the consolidation prompt.

    Args:
        outputs: List of reasoning model outputs

    Returns:
        Formatted string with numbered outputs
    """
    formatted_parts: list[str] = []

    for i, output in enumerate(outputs, start=1):
        formatted_parts.append(f"--- Output {i} ---\n{output}")

    return "\n\n".join(formatted_parts)


def build_consolidation_prompt(outputs: list[str], custom_prompt: str | None = None) -> str:
    """Build the full consolidation prompt with formatted outputs.

    Args:
        outputs: List of reasoning model outputs
        custom_prompt: Optional custom prompt template (must contain {outputs} placeholder)

    Returns:
        Complete prompt string ready for the agent
    """
    formatted_outputs = format_outputs_for_prompt(outputs)
    prompt_template = custom_prompt if custom_prompt is not None else DEFAULT_CONSOLIDATION_PROMPT

    return prompt_template.format(outputs=formatted_outputs)
