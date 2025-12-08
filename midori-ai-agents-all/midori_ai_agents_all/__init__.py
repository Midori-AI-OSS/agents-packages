"""
midori-ai-agents-all

Meta-package bundling all Midori AI agent packages with embedded documentation.
"""

from midori_ai_agents_all.docs_registry import AGENT_BASE_DOCS
from midori_ai_agents_all.docs_registry import AGENT_CONTEXT_MANAGER_DOCS
from midori_ai_agents_all.docs_registry import AGENT_HUGGINGFACE_DOCS
from midori_ai_agents_all.docs_registry import AGENT_LANGCHAIN_DOCS
from midori_ai_agents_all.docs_registry import AGENT_OPENAI_DOCS
from midori_ai_agents_all.docs_registry import COMPACTOR_DOCS
from midori_ai_agents_all.docs_registry import CONTEXT_BRIDGE_DOCS
from midori_ai_agents_all.docs_registry import MEDIA_LIFECYCLE_DOCS
from midori_ai_agents_all.docs_registry import MEDIA_REQUEST_DOCS
from midori_ai_agents_all.docs_registry import MEDIA_VAULT_DOCS
from midori_ai_agents_all.docs_registry import MOOD_ENGINE_DOCS
from midori_ai_agents_all.docs_registry import RERANKER_DOCS
from midori_ai_agents_all.docs_registry import VECTOR_MANAGER_DOCS
from midori_ai_agents_all.docs_registry import list_all_docs

from midori_ai_agents_all.version import __version__


__all__ = ["AGENT_BASE_DOCS", "AGENT_CONTEXT_MANAGER_DOCS", "AGENT_HUGGINGFACE_DOCS", "AGENT_LANGCHAIN_DOCS", "AGENT_OPENAI_DOCS", "COMPACTOR_DOCS", "CONTEXT_BRIDGE_DOCS", "MEDIA_LIFECYCLE_DOCS", "MEDIA_REQUEST_DOCS", "MEDIA_VAULT_DOCS", "MOOD_ENGINE_DOCS", "RERANKER_DOCS", "VECTOR_MANAGER_DOCS", "__version__", "list_all_docs"]
