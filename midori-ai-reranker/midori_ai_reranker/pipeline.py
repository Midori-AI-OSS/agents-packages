"""Main reranker pipeline using DocumentCompressorPipeline."""

from typing import Optional

from langchain_classic.retrievers.document_compressors.base import DocumentCompressorPipeline
from langchain_core.embeddings import Embeddings

from midori_ai_logger import MidoriAiLogger

from .backends.local import LocalReranker
from .config import RerankerConfig
from .filters.redundant import RedundantFilter
from .filters.relevance import RelevanceFilter


logger = MidoriAiLogger(__name__)


class FilterPipeline:
    """Custom filter pipeline for document compression.

    Allows building custom filter chains with RedundantFilter, RelevanceFilter,
    and optional LLMReranker components.

    Attributes:
        embeddings: Embeddings function for similarity comparison
        filters: List of filter components
    """

    def __init__(self, embeddings: Embeddings, filters: Optional[list] = None):
        """Initialize filter pipeline.

        Args:
            embeddings: Embeddings function for similarity comparison
            filters: Optional list of filter components (RedundantFilter, RelevanceFilter, etc.)
        """
        self.embeddings = embeddings
        self.filters = filters or []
        self._pipeline = self._build_pipeline()

    def _build_pipeline(self) -> DocumentCompressorPipeline:
        """Build LangChain DocumentCompressorPipeline from filters."""
        transformers = []
        for filter_obj in self.filters:
            if hasattr(filter_obj, "get_langchain_filter"):
                transformers.append(filter_obj.get_langchain_filter())
            else:
                logger.rprint(f"Filter {filter_obj} does not have get_langchain_filter method", mode="warning")

        return DocumentCompressorPipeline(transformers=transformers)

    async def compress(self, query: str, documents: list[str], max_results: Optional[int] = None) -> list[str]:
        """Compress documents using the filter pipeline.

        Args:
            query: The query to compress documents for
            documents: List of document texts to compress
            max_results: Optional limit on number of results to return

        Returns:
            Compressed list of document texts
        """
        reranker = LocalReranker(embeddings=self.embeddings, pipeline=self._pipeline)
        return await reranker.rerank(query, documents, max_results)


class DocumentReranker:
    """Main document reranker using LangChain's compression pipeline.

    This class provides a high-level interface for reranking documents with
    configurable filters (redundant filter → relevance filter).

    Attributes:
        embeddings: Embeddings function for similarity comparison
        config: RerankerConfig with threshold settings
    """

    def __init__(self, embeddings: Embeddings, relevance_threshold: float = 0.2, config: Optional[RerankerConfig] = None):
        """Initialize document reranker.

        Args:
            embeddings: Embeddings function for similarity comparison
            relevance_threshold: Base relevance threshold (default 0.2)
            config: Optional RerankerConfig for advanced settings
        """
        self.embeddings = embeddings
        self.config = config or RerankerConfig(relevance_threshold=relevance_threshold)
        self._redundant_filter = RedundantFilter(embeddings=embeddings)
        self._relevance_filter = RelevanceFilter(embeddings=embeddings, threshold=self.config.relevance_threshold)
        self._pipeline = self._build_default_pipeline()

    def _build_default_pipeline(self) -> FilterPipeline:
        """Build the default production filter pipeline."""
        filters = []
        if self.config.enable_redundant_filter:
            filters.append(self._redundant_filter)
        if self.config.enable_relevance_filter:
            filters.append(self._relevance_filter)

        return FilterPipeline(embeddings=self.embeddings, filters=filters)

    async def rerank(self, question: str, items: list[str], similarity_threshold_mod: float = 0.0, max_results: Optional[int] = None) -> list[str]:
        """Rerank documents using the filter pipeline.

        Args:
            question: The query to rerank documents for
            items: List of document texts to rerank
            similarity_threshold_mod: Per-query threshold modifier (default 0.0)
            max_results: Optional limit on number of results to return

        Returns:
            Filtered and reranked list of document texts
        """
        effective_threshold = self.config.relevance_threshold + similarity_threshold_mod

        if effective_threshold != self._relevance_filter.threshold:
            self._relevance_filter.update_threshold(effective_threshold)
            self._pipeline = self._build_default_pipeline()

        limited_items = items[: self.config.max_items] if len(items) > self.config.max_items else items

        logger.rprint(f"Reranking {len(limited_items)} items with threshold {effective_threshold}", mode="info")

        return await self._pipeline.compress(question, limited_items, max_results)
