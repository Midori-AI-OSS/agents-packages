"""Tests for pipeline stages."""

import pytest

from unittest.mock import AsyncMock

from midori_ai_agents_demo import PipelineRequest
from midori_ai_agents_demo import StageType

from midori_ai_agents_demo.models import StageContext

from midori_ai_agents_demo.stages import CompactionStage
from midori_ai_agents_demo.stages import FinalResponseStage
from midori_ai_agents_demo.stages import PreprocessingStage
from midori_ai_agents_demo.stages import RerankingStage
from midori_ai_agents_demo.stages import WorkingAwarenessStage


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


@pytest.fixture
def sample_context():
    """Create a sample stage context for testing."""
    request = PipelineRequest(prompt="Test prompt", context="Test context", constraints=["Constraint 1", "Constraint 2"])

    return StageContext(request=request, previous_results=[], shared_data={}, cache_enabled=True)


@pytest.mark.asyncio
async def test_preprocessing_stage(mock_agent, sample_context):
    """Test the preprocessing stage."""
    stage = PreprocessingStage(agent=mock_agent, enabled=True)

    assert stage.stage_type == StageType.PREPROCESSING

    result = await stage.execute(sample_context)

    assert result.status.value == "completed"
    assert result.output is not None
    assert mock_agent.execute_with_reasoning.called


@pytest.mark.asyncio
async def test_preprocessing_stage_disabled(mock_agent, sample_context):
    """Test that disabled preprocessing stage is skipped."""
    stage = PreprocessingStage(agent=mock_agent, enabled=False)

    result = await stage.execute(sample_context)

    assert result.status.value == "skipped"
    assert not mock_agent.execute_with_reasoning.called


@pytest.mark.asyncio
async def test_working_awareness_stage(mock_agent, sample_context):
    """Test the working awareness stage."""
    stage = WorkingAwarenessStage(agent=mock_agent, num_perspectives=2, enabled=True)

    assert stage.stage_type == StageType.WORKING_AWARENESS

    result = await stage.execute(sample_context)

    assert result.status.value == "completed"
    assert result.output is not None
    assert mock_agent.execute_with_reasoning.call_count == 2


@pytest.mark.asyncio
async def test_compaction_stage(mock_compactor, sample_context):
    """Test the compaction stage."""
    stage = CompactionStage(compactor=mock_compactor, enabled=True)

    assert stage.stage_type == StageType.COMPACTION

    result = await stage.execute(sample_context)

    assert result.status.value == "completed"


@pytest.mark.asyncio
async def test_reranking_stage(mock_reranker, sample_context):
    """Test the reranking stage."""
    stage = RerankingStage(reranker=mock_reranker, enabled=True)

    assert stage.stage_type == StageType.RERANKING

    result = await stage.execute(sample_context)

    assert result.status.value == "completed"


@pytest.mark.asyncio
async def test_final_response_stage(mock_agent, sample_context):
    """Test the final response stage."""
    stage = FinalResponseStage(agent=mock_agent, enabled=True)

    assert stage.stage_type == StageType.FINAL_RESPONSE

    result = await stage.execute(sample_context)

    assert result.status.value == "completed"
    assert result.output is not None
    assert mock_agent.execute_with_reasoning.called
