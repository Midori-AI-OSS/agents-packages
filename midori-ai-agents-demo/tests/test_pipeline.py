"""Tests for the main pipeline orchestrator."""

import pytest

from unittest.mock import AsyncMock

from midori_ai_agents_demo import PipelineConfig
from midori_ai_agents_demo import PipelineRequest
from midori_ai_agents_demo import ReasoningPipeline


@pytest.fixture
def mock_agent():
    """Create a mock agent for testing."""
    agent = AsyncMock()

    agent.execute_with_reasoning = AsyncMock()

    mock_response = AsyncMock()

    mock_response.text = "Mock response from agent"

    agent.execute_with_reasoning.return_value = mock_response

    return agent


@pytest.fixture
def mock_compactor():
    """Create a mock compactor for testing."""
    compactor = AsyncMock()

    compactor.compact = AsyncMock(return_value="Compacted output")

    return compactor


@pytest.fixture
def mock_reranker():
    """Create a mock reranker for testing."""
    reranker = AsyncMock()

    mock_result = AsyncMock()

    mock_result.document = "Top ranked result"

    reranker.rerank = AsyncMock(return_value=[mock_result])

    return reranker


@pytest.mark.asyncio
async def test_pipeline_basic_execution(mock_agent, mock_compactor, mock_reranker):
    """Test basic pipeline execution."""
    config = PipelineConfig(enable_preprocessing=True, enable_working_awareness=False, enable_compaction=False, enable_reranking=False, enable_metrics=False, enable_tracing=False)

    pipeline = ReasoningPipeline(agent=mock_agent, config=config, compactor=mock_compactor, reranker=mock_reranker)

    result = await pipeline.process("Test prompt")

    assert result is not None
    assert result.final_response is not None
    assert len(result.stages) > 0
    assert result.total_duration_ms > 0


@pytest.mark.asyncio
async def test_pipeline_with_all_stages(mock_agent, mock_compactor, mock_reranker):
    """Test pipeline with all stages enabled."""
    config = PipelineConfig(enable_preprocessing=True, enable_working_awareness=True, enable_compaction=True, enable_reranking=True, enable_metrics=True, enable_tracing=True)

    pipeline = ReasoningPipeline(agent=mock_agent, config=config, compactor=mock_compactor, reranker=mock_reranker)

    request = PipelineRequest(prompt="Test prompt", context="Test context")

    result = await pipeline.process(request)

    assert result is not None
    assert result.final_response is not None
    assert len(result.stages) >= 5
    assert result.request == request


@pytest.mark.asyncio
async def test_pipeline_with_string_request(mock_agent, mock_compactor, mock_reranker):
    """Test pipeline accepts string requests."""
    config = PipelineConfig(enable_preprocessing=True)

    pipeline = ReasoningPipeline(agent=mock_agent, config=config, compactor=mock_compactor, reranker=mock_reranker)

    result = await pipeline.process("Simple string prompt")

    assert result is not None
    assert result.request.prompt == "Simple string prompt"


@pytest.mark.asyncio
async def test_pipeline_metrics_collection(mock_agent, mock_compactor, mock_reranker):
    """Test that metrics are collected when enabled."""
    config = PipelineConfig(enable_preprocessing=True, enable_metrics=True)

    pipeline = ReasoningPipeline(agent=mock_agent, config=config, compactor=mock_compactor, reranker=mock_reranker)

    result = await pipeline.process("Test prompt")

    assert "metrics" in result.metadata


@pytest.mark.asyncio
async def test_pipeline_tracing(mock_agent, mock_compactor, mock_reranker):
    """Test that tracing is enabled when configured."""
    config = PipelineConfig(enable_preprocessing=True, enable_tracing=True)

    pipeline = ReasoningPipeline(agent=mock_agent, config=config, compactor=mock_compactor, reranker=mock_reranker)

    result = await pipeline.process("Test prompt")

    assert "trace_id" in result.metadata
