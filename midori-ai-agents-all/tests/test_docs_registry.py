"""Tests for midori-ai-agents-all package."""

import pytest

from midori_ai_agents_all import AGENT_BASE_DOCS
from midori_ai_agents_all import AGENT_CONTEXT_MANAGER_DOCS
from midori_ai_agents_all import AGENT_HUGGINGFACE_DOCS
from midori_ai_agents_all import AGENT_LANGCHAIN_DOCS
from midori_ai_agents_all import AGENT_OPENAI_DOCS
from midori_ai_agents_all import COMPACTOR_DOCS
from midori_ai_agents_all import CONTEXT_BRIDGE_DOCS
from midori_ai_agents_all import MEDIA_LIFECYCLE_DOCS
from midori_ai_agents_all import MEDIA_REQUEST_DOCS
from midori_ai_agents_all import MEDIA_VAULT_DOCS
from midori_ai_agents_all import MOOD_ENGINE_DOCS
from midori_ai_agents_all import RERANKER_DOCS
from midori_ai_agents_all import VECTOR_MANAGER_DOCS
from midori_ai_agents_all import __version__
from midori_ai_agents_all import list_all_docs


def test_all_docs_present():
    """Verify all package docs are embedded."""
    docs = list_all_docs()
    expected_packages = [
        "midori-ai-agent-base",
        "midori-ai-agent-context-manager",
        "midori-ai-agent-huggingface",
        "midori-ai-agent-langchain",
        "midori-ai-agent-openai",
        "midori-ai-compactor",
        "midori-ai-context-bridge",
        "midori-ai-media-lifecycle",
        "midori-ai-media-request",
        "midori-ai-media-vault",
        "midori-ai-mood-engine",
        "midori-ai-reranker",
        "midori-ai-vector-manager",
    ]

    for pkg in expected_packages:
        assert pkg in docs, f"Missing package: {pkg}"
        assert len(docs[pkg]) > 0, f"Empty docs for package: {pkg}"


def test_doc_constants_accessible():
    """Verify individual doc constants can be imported and are non-empty."""
    assert len(AGENT_BASE_DOCS) > 0
    assert len(AGENT_CONTEXT_MANAGER_DOCS) > 0
    assert len(AGENT_HUGGINGFACE_DOCS) > 0
    assert len(AGENT_LANGCHAIN_DOCS) > 0
    assert len(AGENT_OPENAI_DOCS) > 0
    assert len(COMPACTOR_DOCS) > 0
    assert len(CONTEXT_BRIDGE_DOCS) > 0
    assert len(MEDIA_LIFECYCLE_DOCS) > 0
    assert len(MEDIA_REQUEST_DOCS) > 0
    assert len(MEDIA_VAULT_DOCS) > 0
    assert len(MOOD_ENGINE_DOCS) > 0
    assert len(RERANKER_DOCS) > 0
    assert len(VECTOR_MANAGER_DOCS) > 0


def test_doc_headers():
    """Verify each doc string starts with expected header format."""
    assert "midori-ai-agent-base" in AGENT_BASE_DOCS
    assert "midori-ai-compactor" in COMPACTOR_DOCS
    assert "midori-ai-vector-manager" in VECTOR_MANAGER_DOCS


def test_list_all_docs_count():
    """Verify list_all_docs returns all 13 packages."""
    docs = list_all_docs()
    assert len(docs) == 13, f"Expected 13 packages, got {len(docs)}"


def test_version_accessible():
    """Verify version string is accessible."""
    assert __version__ is not None
    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_docs_contain_usage_examples():
    """Verify docs contain Python code examples."""
    assert "```python" in AGENT_BASE_DOCS
    assert "```python" in COMPACTOR_DOCS


def test_no_import_errors():
    """Verify all imports work without errors."""
    try:
        from midori_ai_agents_all import AGENT_BASE_DOCS
        from midori_ai_agents_all import AGENT_CONTEXT_MANAGER_DOCS
        from midori_ai_agents_all import AGENT_HUGGINGFACE_DOCS
        from midori_ai_agents_all import AGENT_LANGCHAIN_DOCS
        from midori_ai_agents_all import AGENT_OPENAI_DOCS
        from midori_ai_agents_all import COMPACTOR_DOCS
        from midori_ai_agents_all import CONTEXT_BRIDGE_DOCS
        from midori_ai_agents_all import MEDIA_LIFECYCLE_DOCS
        from midori_ai_agents_all import MEDIA_REQUEST_DOCS
        from midori_ai_agents_all import MEDIA_VAULT_DOCS
        from midori_ai_agents_all import MOOD_ENGINE_DOCS
        from midori_ai_agents_all import RERANKER_DOCS
        from midori_ai_agents_all import VECTOR_MANAGER_DOCS
        from midori_ai_agents_all import list_all_docs
    except ImportError as e:
        pytest.fail(f"Import error: {e}")


def test_docs_match_package_names():
    """Verify docs dict keys match package names."""
    docs = list_all_docs()
    expected_keys = {
        "midori-ai-agent-base",
        "midori-ai-agent-context-manager",
        "midori-ai-agent-huggingface",
        "midori-ai-agent-langchain",
        "midori-ai-agent-openai",
        "midori-ai-compactor",
        "midori-ai-context-bridge",
        "midori-ai-media-lifecycle",
        "midori-ai-media-request",
        "midori-ai-media-vault",
        "midori-ai-mood-engine",
        "midori-ai-reranker",
        "midori-ai-vector-manager",
    }
    assert set(docs.keys()) == expected_keys
