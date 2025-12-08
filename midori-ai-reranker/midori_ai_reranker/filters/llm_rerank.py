"""Optional LLM-based reranking using midori-ai-agent-base."""

from typing import Optional

from midori_ai_agent_base.protocol import MidoriAiAgentProtocol


class LLMReranker:
    """Optional LLM-based reranking using Midori AI agent base.

    This is a heavyweight operation that uses an LLM to intelligently reorder results.
    Should be used sparingly and only when embedding-based filters are insufficient.

    Attributes:
        agent: MidoriAiAgentProtocol instance from midori-ai-agent-base
    """

    def __init__(self, agent: MidoriAiAgentProtocol):
        """Initialize LLM reranker.

        Args:
            agent: MidoriAiAgentProtocol instance from get_agent() factory
        """
        self.agent = agent

    async def rerank(self, query: str, documents: list[str], top_k: Optional[int] = None) -> list[str]:
        """Rerank documents using LLM.

        Args:
            query: The query to rerank documents for
            documents: List of document texts to rerank
            top_k: Optional limit on number of results to return

        Returns:
            Reranked list of document texts
        """
        if not documents:
            return []

        prompt = self._build_rerank_prompt(query, documents)

        response = await self.agent.generate(prompt)

        reranked_indices = self._parse_rerank_response(response, len(documents))

        reranked = [documents[i] for i in reranked_indices if i < len(documents)]

        if top_k is not None:
            reranked = reranked[:top_k]

        return reranked

    def _build_rerank_prompt(self, query: str, documents: list[str]) -> str:
        """Build reranking prompt for LLM."""
        doc_list = "\n".join([f"{i+1}. {doc}" for i, doc in enumerate(documents)])
        return f"""Given the query: "{query}"

Rerank the following documents by relevance (most relevant first).
Return only the document numbers in order, separated by commas.

Documents:
{doc_list}

Ranking (comma-separated numbers):"""

    def _parse_rerank_response(self, response: str, num_docs: int) -> list[int]:
        """Parse LLM response to extract document indices."""
        try:
            indices_str = response.strip().split("\n")[0]
            indices = [int(x.strip()) - 1 for x in indices_str.split(",") if x.strip().isdigit()]
            return [i for i in indices if 0 <= i < num_docs]
        except Exception:
            return list(range(num_docs))
