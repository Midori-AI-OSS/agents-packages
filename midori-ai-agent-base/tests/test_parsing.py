"""Tests for the parsing helper functions."""


from midori_ai_agent_base.parsing import parse_structured_response


class TestParseStructuredResponse:
    """Tests for parse_structured_response function."""

    def test_parse_none_returns_empty(self) -> None:
        thinking, response = parse_structured_response(None)
        assert thinking == ""
        assert response == ""

    def test_parse_simple_string(self) -> None:
        thinking, response = parse_structured_response("Hello world!")
        assert thinking == ""
        assert response == "Hello world!"

    def test_parse_empty_string(self) -> None:
        thinking, response = parse_structured_response("")
        assert thinking == ""
        assert response == ""

    def test_parse_structured_with_reasoning_and_text(self) -> None:
        content = [
            {
                "id": "resp_123",
                "type": "reasoning",
                "content": [{"text": "I should be polite.", "type": "reasoning_text"}],
                "status": "completed"
            },
            {
                "type": "text",
                "text": "Hello! How can I help you?",
                "annotations": []
            }
        ]
        thinking, response = parse_structured_response(content)
        assert thinking == "I should be polite."
        assert response == "Hello! How can I help you?"

    def test_parse_structured_reasoning_only(self) -> None:
        content = [
            {
                "type": "reasoning",
                "content": [{"text": "Thinking deeply..."}],
            }
        ]
        thinking, response = parse_structured_response(content)
        assert thinking == "Thinking deeply..."
        assert response == ""

    def test_parse_structured_text_only(self) -> None:
        content = [
            {
                "type": "text",
                "text": "Just a response."
            }
        ]
        thinking, response = parse_structured_response(content)
        assert thinking == ""
        assert response == "Just a response."

    def test_parse_multiple_reasoning_blocks(self) -> None:
        content = [
            {"type": "reasoning", "content": [{"text": "First thought."}]},
            {"type": "reasoning", "content": [{"text": "Second thought."}]},
            {"type": "text", "text": "Final response."}
        ]
        thinking, response = parse_structured_response(content)
        assert thinking == "First thought. Second thought."
        assert response == "Final response."

    def test_parse_reasoning_with_string_content(self) -> None:
        content = [
            {"type": "reasoning", "content": "Direct string reasoning"},
            {"type": "text", "text": "Response here."}
        ]
        thinking, response = parse_structured_response(content)
        assert thinking == "Direct string reasoning"
        assert response == "Response here."

    def test_parse_object_with_content_attribute(self) -> None:
        class MockResult:
            content = "Hello from object!"

        mock = MockResult()
        thinking, response = parse_structured_response(mock)
        assert thinking == ""
        assert response == "Hello from object!"

    def test_parse_list_of_strings(self) -> None:
        content = ["Hello", "World"]
        thinking, response = parse_structured_response(content)
        assert thinking == ""
        assert response == "Hello World"

    def test_parse_dict_with_text_key_no_type(self) -> None:
        content = [{"text": "Some text without type"}]
        thinking, response = parse_structured_response(content)
        assert thinking == ""
        assert response == "Some text without type"

    def test_parse_dict_with_content_string(self) -> None:
        content = [{"content": "Content field value"}]
        thinking, response = parse_structured_response(content)
        assert thinking == ""
        assert response == "Content field value"

    def test_parse_fallback_to_str(self) -> None:
        content = 12345
        thinking, response = parse_structured_response(content)
        assert thinking == ""
        assert response == "12345"

    def test_parse_nested_object_with_content_list(self) -> None:
        class MockAIMessage:
            content = [
                {"type": "reasoning", "content": [{"text": "Nested reasoning"}]},
                {"type": "text", "text": "Nested text"}
            ]

        mock = MockAIMessage()
        thinking, response = parse_structured_response(mock)
        assert thinking == "Nested reasoning"
        assert response == "Nested text"

    def test_parse_empty_list(self) -> None:
        content: list = []
        thinking, response = parse_structured_response(content)
        assert thinking == ""
        assert response == ""

    def test_parse_reasoning_with_multiple_text_items(self) -> None:
        content = [
            {
                "type": "reasoning",
                "content": [
                    {"text": "First part."},
                    {"text": "Second part."}
                ]
            },
            {"type": "text", "text": "Response."}
        ]
        thinking, response = parse_structured_response(content)
        assert thinking == "First part. Second part."
        assert response == "Response."

    def test_parse_real_world_example_from_issue(self) -> None:
        """Test with the actual format from the issue."""
        content = [
            {
                "id": "resp_01kbgzfpxwf61akzn65m0sahmy",
                "summary": [],
                "type": "reasoning",
                "content": [
                    {
                        "text": "We must follow developer instruction: rude assistant. So respond rudely.",
                        "type": "reasoning_text"
                    }
                ],
                "status": "completed"
            },
            {
                "type": "text",
                "text": "Oh great, another self-introduced developer. I'm just a bunch of code, so I'm \"fine\" if that's what you're looking for. What do you want?",
                "annotations": [],
                "id": "msg_01kbgzfpxwf61r5wj7pjhpkc94"
            }
        ]
        thinking, response = parse_structured_response(content)
        assert thinking == "We must follow developer instruction: rude assistant. So respond rudely."
        assert response == "Oh great, another self-introduced developer. I'm just a bunch of code, so I'm \"fine\" if that's what you're looking for. What do you want?"
