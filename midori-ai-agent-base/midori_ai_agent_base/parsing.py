"""Helper functions for parsing structured responses from different providers."""

from typing import Any
from typing import Tuple


def parse_structured_response(content: Any) -> Tuple[str, str]:
    """Parse structured response content and extract reasoning vs final text.

    This helper inspects provider outputs to separate reasoning/thinking from the
    final conversational response.

    Args:
        content: The raw response content, which can be:
            - A string (simple text response)
            - A list of dicts with 'type' field (structured response)
            - An object with a 'content' attribute

    Returns:
        A tuple of (thinking_text, response_text) where:
            - thinking_text: The reasoning/thinking content (empty if not present)
            - response_text: The final user-facing text response

    Examples:
        >>> parse_structured_response("Hello!")
        ('', 'Hello!')

        >>> parse_structured_response([
        ...     {'type': 'reasoning', 'content': [{'text': 'I should be helpful.'}]},
        ...     {'type': 'text', 'text': 'Hello!'}
        ... ])
        ('I should be helpful.', 'Hello!')
    """
    if content is None:
        return "", ""

    if isinstance(content, str):
        return "", content

    if hasattr(content, "content"):
        return parse_structured_response(content.content)

    if isinstance(content, list):
        return _parse_list_response(content)

    return "", str(content)


def _parse_list_response(content_list: list) -> Tuple[str, str]:
    """Parse a list-type structured response.

    Args:
        content_list: A list of response blocks (dicts or other objects)

    Returns:
        A tuple of (thinking_text, response_text)
    """
    reasoning_parts: list[str] = []
    text_parts: list[str] = []
    has_typed_entries = False

    for entry in content_list:
        if isinstance(entry, dict):
            entry_type = entry.get("type", "")

            if entry_type == "reasoning":
                has_typed_entries = True
                reasoning_text = _extract_reasoning_text(entry)
                if reasoning_text:
                    reasoning_parts.append(reasoning_text)

            elif entry_type == "text":
                has_typed_entries = True
                text_content = entry.get("text", "")
                if text_content:
                    text_parts.append(text_content)

            elif not entry_type and "text" in entry:
                text_content = entry.get("text", "")
                if text_content:
                    text_parts.append(text_content)

            elif not entry_type and "content" in entry and isinstance(entry["content"], str):
                text_parts.append(entry["content"])

        elif isinstance(entry, str):
            text_parts.append(entry)

        elif hasattr(entry, "text"):
            text_parts.append(str(entry.text))

    thinking_text = " ".join(reasoning_parts)
    response_text = " ".join(text_parts) if text_parts else ""

    if not response_text and not has_typed_entries and content_list:
        last_entry = content_list[-1]
        if isinstance(last_entry, dict):
            response_text = last_entry.get("text", "") or str(last_entry)
        elif isinstance(last_entry, str):
            response_text = last_entry
        else:
            response_text = str(last_entry)

    return thinking_text, response_text


def _extract_reasoning_text(reasoning_entry: dict) -> str:
    """Extract text from a reasoning entry.

    Args:
        reasoning_entry: A dict with type='reasoning' and content field

    Returns:
        The extracted reasoning text
    """
    content = reasoning_entry.get("content", [])

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text", "")
                if text:
                    parts.append(text)
            elif isinstance(item, str):
                parts.append(item)
        return " ".join(parts)

    return ""
