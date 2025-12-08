# midori-ai-agents-all Documentation

Meta-package bundling all Midori AI agent packages with embedded documentation.

## Overview

This meta-package provides:
1. **All Midori AI packages** as dependencies - install one package to get them all
2. **Embedded documentation** - access any package's docs programmatically without cloning the repo
3. **Easy exploration** - discover and learn about the entire Midori AI ecosystem from Python

## Included Packages

This meta-package installs and provides documentation for:

- `midori-ai-agent-base` - Common protocol and data models
- `midori-ai-agent-context-manager` - Context management and memory persistence
- `midori-ai-agent-huggingface` - HuggingFace local inference backend
- `midori-ai-agent-langchain` - Langchain backend implementation
- `midori-ai-agent-openai` - OpenAI Agents SDK backend
- `midori-ai-compactor` - Multi-model reasoning consolidation
- `midori-ai-context-bridge` - Persistent thinking cache with decay
- `midori-ai-media-lifecycle` - Time-based media decay and cleanup
- `midori-ai-media-request` - Type-safe media request/response interface
- `midori-ai-media-vault` - Encrypted media storage
- `midori-ai-mood-engine` - Comprehensive mood management system
- `midori-ai-reranker` - Document reranking and filtering
- `midori-ai-vector-manager` - Vector storage abstraction

## Usage

### Access Individual Package Documentation

```python
from midori_ai_agents_all import AGENT_BASE_DOCS, COMPACTOR_DOCS

# Print full documentation for a package
print(COMPACTOR_DOCS)

# Search for specific information
if "consolidation" in COMPACTOR_DOCS:
    print("Compactor handles consolidation")
```

### List All Available Documentation

```python
from midori_ai_agents_all import list_all_docs

# Get dictionary of all package docs
all_docs = list_all_docs()

# List all packages
for package_name in all_docs.keys():
    print(f"- {package_name}")

# Print first 200 characters of each package's docs
for package_name, docs_content in all_docs.items():
    print(f"\n=== {package_name} ===")
    print(docs_content[:200])
    print("...")
```

### Search Across All Documentation

```python
from midori_ai_agents_all import list_all_docs

def find_packages_with_keyword(keyword: str) -> list[str]:
    """Find all packages whose documentation contains a keyword."""
    all_docs = list_all_docs()
    matching = []
    
    for package_name, docs_content in all_docs.items():
        if keyword.lower() in docs_content.lower():
            matching.append(package_name)
    
    return matching

# Find packages related to agents
agent_packages = find_packages_with_keyword("agent")
print(f"Packages related to 'agent': {agent_packages}")

# Find packages related to encryption
crypto_packages = find_packages_with_keyword("encrypt")
print(f"Packages with encryption: {crypto_packages}")
```

### Build a Package Explorer

```python
from midori_ai_agents_all import list_all_docs

def explore_package(package_name: str):
    """Display documentation for a specific package."""
    all_docs = list_all_docs()
    
    if package_name in all_docs:
        print(f"\n{'='*60}")
        print(f"Documentation for: {package_name}")
        print(f"{'='*60}\n")
        print(all_docs[package_name])
    else:
        print(f"Package '{package_name}' not found.")
        print(f"Available packages: {', '.join(all_docs.keys())}")

# Explore a specific package
explore_package("midori-ai-compactor")
```

### Extract Code Examples from Documentation

```python
from midori_ai_agents_all import list_all_docs
import re

def extract_code_examples(package_name: str) -> list[str]:
    """Extract all Python code examples from a package's documentation."""
    all_docs = list_all_docs()
    
    if package_name not in all_docs:
        return []
    
    docs = all_docs[package_name]
    
    # Find all code blocks marked as python
    pattern = r'```python\n(.*?)```'
    examples = re.findall(pattern, docs, re.DOTALL)
    
    return examples

# Get all code examples from compactor docs
examples = extract_code_examples("midori-ai-compactor")
print(f"Found {len(examples)} code examples in compactor docs")

for i, example in enumerate(examples, 1):
    print(f"\n--- Example {i} ---")
    print(example[:200])  # Print first 200 chars
```

### Integration with External Tools

```python
from midori_ai_agents_all import list_all_docs

async def answer_question_with_docs(question: str, llm):
    """Use an LLM to answer questions about Midori AI packages."""
    all_docs = list_all_docs()
    
    # Combine all docs into context
    context = "\n\n".join([
        f"# {pkg}\n{docs}"
        for pkg, docs in all_docs.items()
    ])
    
    # Build prompt
    prompt = f"""
You are a helpful assistant answering questions about Midori AI packages.

Context (package documentation):
{context[:50000]}  # Truncate if needed

Question: {question}

Answer:"""
    
    # Send to LLM
    response = await llm.generate(prompt)
    return response

# Example usage:
# answer = await answer_question_with_docs(
#     "How do I use the compactor package?",
#     my_llm
# )
```

## Available Documentation Constants

Each package's documentation is available as a constant:

- `AGENT_BASE_DOCS` - midori-ai-agent-base documentation
- `AGENT_CONTEXT_MANAGER_DOCS` - midori-ai-agent-context-manager documentation
- `AGENT_HUGGINGFACE_DOCS` - midori-ai-agent-huggingface documentation
- `AGENT_LANGCHAIN_DOCS` - midori-ai-agent-langchain documentation
- `AGENT_OPENAI_DOCS` - midori-ai-agent-openai documentation
- `COMPACTOR_DOCS` - midori-ai-compactor documentation
- `CONTEXT_BRIDGE_DOCS` - midori-ai-context-bridge documentation
- `MEDIA_LIFECYCLE_DOCS` - midori-ai-media-lifecycle documentation
- `MEDIA_REQUEST_DOCS` - midori-ai-media-request documentation
- `MEDIA_VAULT_DOCS` - midori-ai-media-vault documentation
- `MOOD_ENGINE_DOCS` - midori-ai-mood-engine documentation
- `RERANKER_DOCS` - midori-ai-reranker documentation
- `VECTOR_MANAGER_DOCS` - midori-ai-vector-manager documentation

## Benefits

1. **One-stop installation** - Install all Midori AI packages with a single command
2. **Offline documentation access** - No need to clone the repo or browse GitHub
3. **Programmatic docs exploration** - Build tools that analyze or search documentation
4. **LLM integration** - Feed docs directly to LLMs for context-aware assistance
5. **Dependency management** - Ensures all packages are compatible versions

## Package Version

```python
from midori_ai_agents_all import __version__

print(f"midori-ai-agents-all version: {__version__}")
```

## Best Practices

1. **Search before exploring** - Use `list_all_docs()` to find relevant packages
2. **Extract code examples** - Use regex to find runnable code snippets
3. **Cache docs locally** - If accessing frequently, store docs in memory
4. **Truncate for LLMs** - Context windows are limited; send only relevant docs
5. **Keep updated** - Reinstall periodically to get latest documentation

## Notes

- Documentation is embedded at build time and reflects the state of packages at that moment
- Each package's full docs.md content is included
- No network access required to read documentation
- All documentation is UTF-8 encoded text
