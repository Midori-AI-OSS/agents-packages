"""Relevance filter wrapper for EmbeddingsFilter."""


from langchain_classic.retrievers.document_compressors.embeddings_filter import EmbeddingsFilter
from langchain_core.embeddings import Embeddings


class RelevanceFilter:
    """Wrapper for LangChain's EmbeddingsFilter.

    Filters documents below a relevance threshold based on embedding similarity.
    Should be applied AFTER RedundantFilter in the pipeline.

    Attributes:
        embeddings: Embeddings function for similarity comparison
        threshold: Relevance threshold (default 0.2)
    """

    def __init__(self, embeddings: Embeddings, threshold: float = 0.2):
        """Initialize relevance filter.

        Args:
            embeddings: Embeddings function for similarity comparison
            threshold: Relevance threshold (default 0.2)
        """
        self.embeddings = embeddings
        self.threshold = threshold
        self._filter = EmbeddingsFilter(embeddings=embeddings, similarity_threshold=threshold)

    def get_langchain_filter(self) -> EmbeddingsFilter:
        """Get the underlying LangChain filter for pipeline composition."""
        return self._filter

    def update_threshold(self, new_threshold: float) -> None:
        """Update the relevance threshold dynamically.

        Args:
            new_threshold: New threshold value
        """
        self.threshold = new_threshold
        self._filter = EmbeddingsFilter(embeddings=self.embeddings, similarity_threshold=new_threshold)
