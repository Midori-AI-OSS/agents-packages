"""Local reranking backend using InMemoryVectorStore pattern."""

from typing import Optional

from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors.base import DocumentCompressorPipeline
from langchain_community.vectorstores import InMemoryVectorStore
from langchain_core.embeddings import Embeddings

from midori_ai_logger import MidoriAiLogger


logger = MidoriAiLogger(__name__)


class LocalReranker:
    """Local reranking using InMemoryVectorStore pattern.

    This class handles the LangChain integration for loading raw results into
    a temporary in-memory vector store and applying compression filters.

    Attributes:
        embeddings: Embeddings function for similarity comparison
        pipeline: DocumentCompressorPipeline with filters
    """

    def __init__(self, embeddings: Embeddings, pipeline: DocumentCompressorPipeline):
        """Initialize local reranker.

        Args:
            embeddings: Embeddings function for similarity comparison
            pipeline: DocumentCompressorPipeline with filters
        """
        self.embeddings = embeddings
        self.pipeline = pipeline

    async def rerank(self, query: str, documents: list[str], max_results: Optional[int] = None) -> list[str]:
        """Rerank documents using the filter pipeline.

        Args:
            query: The query to rerank documents for
            documents: List of document texts to rerank
            max_results: Optional limit on number of results to return

        Returns:
            Filtered and reranked list of document texts
        """
        if not documents:
            logger.rprint("No documents to rerank", mode="debug")
            return []

        try:
            sanitized_docs = [doc.encode("utf-8", errors="ignore").decode("utf-8") for doc in documents]

            temp_store = await InMemoryVectorStore.afrom_texts(sanitized_docs, self.embeddings)

            compression_retriever = ContextualCompressionRetriever(base_compressor=self.pipeline, base_retriever=temp_store.as_retriever(search_kwargs={"k": len(documents)}))

            compressed_docs = await compression_retriever.ainvoke(query)

            results = [doc.page_content for doc in compressed_docs]

            if max_results is not None:
                results = results[:max_results]

            logger.rprint(f"Reranked {len(documents)} documents to {len(results)} results", mode="debug")
            return results

        except Exception as e:
            logger.rprint(f"Error during reranking: {e}", mode="error")
            return documents[:max_results] if max_results else documents
