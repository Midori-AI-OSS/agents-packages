"""Tests for midori-ai-reranker package."""

import pytest

from langchain_core.embeddings import Embeddings

from midori_ai_reranker import DEFAULT_CONFIG
from midori_ai_reranker import DocumentReranker
from midori_ai_reranker import FilterPipeline
from midori_ai_reranker import RedundantFilter
from midori_ai_reranker import RelevanceFilter
from midori_ai_reranker import RerankerConfig


class MockEmbeddings(Embeddings):
    """Mock embeddings for testing."""

    async def aembed_documents(self, texts):
        """Mock embedding of multiple documents."""
        return [[0.1, 0.2, 0.3] for _ in texts]

    async def aembed_query(self, text):
        """Mock embedding of a single query."""
        return [0.1, 0.2, 0.3]

    def embed_documents(self, texts):
        """Mock embedding of multiple documents (sync)."""
        return [[0.1, 0.2, 0.3] for _ in texts]

    def embed_query(self, text):
        """Mock embedding of a single query (sync)."""
        return [0.1, 0.2, 0.3]


def test_reranker_config_defaults():
    """Test RerankerConfig default values."""
    config = RerankerConfig()
    assert config.relevance_threshold == 0.2
    assert config.similarity_threshold_mod == 0.0
    assert config.max_items == 50
    assert config.enable_redundant_filter is True
    assert config.enable_relevance_filter is True


def test_reranker_config_effective_threshold():
    """Test RerankerConfig effective threshold calculation."""
    config = RerankerConfig(relevance_threshold=0.2, similarity_threshold_mod=0.3)
    assert config.effective_threshold == 0.5


def test_default_config():
    """Test DEFAULT_CONFIG is available."""
    assert DEFAULT_CONFIG.relevance_threshold == 0.2


def test_redundant_filter_initialization():
    """Test RedundantFilter initialization."""
    embeddings = MockEmbeddings()
    filter_obj = RedundantFilter(embeddings)
    assert filter_obj.embeddings == embeddings
    assert filter_obj.similarity_threshold == 0.95


def test_relevance_filter_initialization():
    """Test RelevanceFilter initialization."""
    embeddings = MockEmbeddings()
    filter_obj = RelevanceFilter(embeddings, threshold=0.3)
    assert filter_obj.embeddings == embeddings
    assert filter_obj.threshold == 0.3


def test_relevance_filter_threshold_update():
    """Test RelevanceFilter threshold update."""
    embeddings = MockEmbeddings()
    filter_obj = RelevanceFilter(embeddings, threshold=0.2)
    assert filter_obj.threshold == 0.2

    filter_obj.update_threshold(0.5)
    assert filter_obj.threshold == 0.5


def test_document_reranker_initialization():
    """Test DocumentReranker initialization."""
    embeddings = MockEmbeddings()
    reranker = DocumentReranker(embeddings, relevance_threshold=0.3)
    assert reranker.embeddings == embeddings
    assert reranker.config.relevance_threshold == 0.3


def test_filter_pipeline_initialization():
    """Test FilterPipeline initialization."""
    embeddings = MockEmbeddings()
    filter1 = RedundantFilter(embeddings)
    filter2 = RelevanceFilter(embeddings, threshold=0.2)

    pipeline = FilterPipeline(embeddings=embeddings, filters=[filter1, filter2])
    assert pipeline.embeddings == embeddings
    assert len(pipeline.filters) == 2


@pytest.mark.asyncio
async def test_document_reranker_empty_items():
    """Test DocumentReranker with empty items list."""
    embeddings = MockEmbeddings()
    reranker = DocumentReranker(embeddings)

    result = await reranker.rerank(question="test query", items=[])
    assert result == []


@pytest.mark.asyncio
async def test_document_reranker_basic_functionality():
    """Test DocumentReranker basic reranking."""
    embeddings = MockEmbeddings()
    reranker = DocumentReranker(embeddings, relevance_threshold=0.2)

    items = ["First document about Python", "Second document about Java", "Third document about Python programming"]

    result = await reranker.rerank(question="What is Python?", items=items)

    assert isinstance(result, list)
    assert len(result) <= len(items)


@pytest.mark.asyncio
async def test_document_reranker_threshold_modifier():
    """Test DocumentReranker with threshold modifier."""
    embeddings = MockEmbeddings()
    reranker = DocumentReranker(embeddings, relevance_threshold=0.2)

    items = ["Document 1", "Document 2", "Document 3"]

    result1 = await reranker.rerank(question="test", items=items, similarity_threshold_mod=0.0)

    result2 = await reranker.rerank(question="test", items=items, similarity_threshold_mod=0.5)

    assert isinstance(result1, list)
    assert isinstance(result2, list)


@pytest.mark.asyncio
async def test_filter_pipeline_compress():
    """Test FilterPipeline compress method."""
    embeddings = MockEmbeddings()
    filter1 = RedundantFilter(embeddings)
    filter2 = RelevanceFilter(embeddings, threshold=0.2)

    pipeline = FilterPipeline(embeddings=embeddings, filters=[filter1, filter2])

    documents = ["Doc 1", "Doc 2", "Doc 3"]
    result = await pipeline.compress(query="test query", documents=documents)

    assert isinstance(result, list)
    assert len(result) <= len(documents)


@pytest.mark.asyncio
async def test_document_reranker_max_items_limit():
    """Test DocumentReranker respects max_items limit."""
    embeddings = MockEmbeddings()
    config = RerankerConfig(max_items=5)
    reranker = DocumentReranker(embeddings, config=config)

    items = [f"Document {i}" for i in range(20)]

    result = await reranker.rerank(question="test", items=items)

    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_document_reranker_max_results():
    """Test DocumentReranker with max_results parameter."""
    embeddings = MockEmbeddings()
    reranker = DocumentReranker(embeddings)

    items = [f"Document {i}" for i in range(10)]

    result = await reranker.rerank(question="test", items=items, max_results=3)

    assert isinstance(result, list)
    assert len(result) <= 3
