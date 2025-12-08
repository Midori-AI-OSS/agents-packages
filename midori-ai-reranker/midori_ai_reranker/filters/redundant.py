"""Redundancy filter wrapper for EmbeddingsRedundantFilter."""


from langchain_community.document_transformers import EmbeddingsRedundantFilter
from langchain_core.embeddings import Embeddings


class RedundantFilter:
    """Wrapper for LangChain's EmbeddingsRedundantFilter.

    Removes semantically similar/duplicate documents using embedding similarity.
    Should be applied BEFORE RelevanceFilter in the pipeline.

    Attributes:
        embeddings: Embeddings function for similarity comparison
        similarity_threshold: Threshold for duplicate detection (default 0.95)
    """

    def __init__(self, embeddings: Embeddings, similarity_threshold: float = 0.95):
        """Initialize redundancy filter.

        Args:
            embeddings: Embeddings function for similarity comparison
            similarity_threshold: Threshold for duplicate detection (default 0.95)
        """
        self.embeddings = embeddings
        self.similarity_threshold = similarity_threshold
        self._filter = EmbeddingsRedundantFilter(embeddings=embeddings, similarity_threshold=similarity_threshold)

    def get_langchain_filter(self) -> EmbeddingsRedundantFilter:
        """Get the underlying LangChain filter for pipeline composition."""
        return self._filter
