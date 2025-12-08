"""Factory function for creating agent backends by configuration."""

from pathlib import Path

from typing import Any
from typing import Optional
from typing import Union

from midori_ai_agent_langchain import LangchainAgent
from midori_ai_agent_openai import OpenAIAgentsAdapter

from .config import AgentConfig
from .config import load_agent_config
from .models import ReasoningEffort
from .protocol import MidoriAiAgentProtocol


async def get_agent(backend: str, model: str, api_key: str, base_url: Optional[str] = None, **kwargs: Any) -> MidoriAiAgentProtocol:
    """Factory function to get the appropriate agent backend.

    Args:
        backend: The backend type ("langchain", "openai", "huggingface")
        model: Model name to use
        api_key: API key for authentication (not required for huggingface)
        base_url: Base URL for the API endpoint (optional, not used for huggingface)
        **kwargs: Additional arguments passed to the backend

    Returns:
        An instance of MidoriAiAgentProtocol

    Raises:
        ValueError: If the backend is unknown

    Example:
        ```python
        agent = await get_agent(
            backend="langchain",
            model="carly-agi-pro",
            api_key="your-api-key",
            base_url="https://api.example.com/v1",
        )
        ```
    """
    if backend == "langchain":
        return LangchainAgent(model=model, api_key=api_key, base_url=base_url or "", **kwargs)

    if backend == "openai":
        return OpenAIAgentsAdapter(model=model, api_key=api_key, base_url=base_url, **kwargs)

    if backend == "huggingface":
        try:
            from midori_ai_agent_huggingface import HuggingFaceLocalAgent
        except ImportError as e:
            raise ImportError("midori-ai-agent-huggingface is not installed. Install it with: uv add 'git+https://github.com/Midori-AI-OSS/Carly-AGI#subdirectory=Rest-Servers/packages/midori-ai-agent-huggingface'") from e
        return HuggingFaceLocalAgent(model=model, **kwargs)

    raise ValueError(f"Unknown agent backend: {backend}. Valid backends are: langchain, openai, huggingface")


async def get_agent_from_config(config_path: Optional[Union[str, Path]] = None, backend: Optional[str] = None, model: Optional[str] = None, api_key: Optional[str] = None, base_url: Optional[str] = None, **kwargs: Any) -> MidoriAiAgentProtocol:
    """Factory function to get an agent from a TOML config file.

    Loads configuration from a TOML file and creates the appropriate agent
    backend. Explicit arguments override values from the config file.

    Args:
        config_path: Path to the TOML config file. If None, searches upward
            from the package directory for a file named `config.toml`.
        backend: Override backend type ("langchain", "openai", "huggingface").
        model: Override model name.
        api_key: Override API key.
        base_url: Override base URL.
        **kwargs: Additional arguments passed to the backend.

    Returns:
        An instance of MidoriAiAgentProtocol

    Raises:
        ValueError: If backend, model, or api_key is missing after config merge.

    Example:
        ```python
        # Load from config.toml with defaults
        agent = await get_agent_from_config()

        # Load from a specific config file
        agent = await get_agent_from_config(config_path="my-config.toml")

        # Override specific values from config
        agent = await get_agent_from_config(model="gpt-4", api_key="sk-...")
        ```
    """
    config = _load_config_from_path(config_path, backend)
    final_backend = backend if backend is not None else config.backend
    final_model = model if model is not None else config.model
    final_api_key = api_key if api_key is not None else config.api_key
    final_base_url = base_url if base_url is not None else config.base_url

    if final_backend is None:
        raise ValueError("backend is required: specify it in config.toml or as an argument")

    if final_model is None:
        raise ValueError("model is required: specify it in config.toml or as an argument")

    if final_api_key is None and final_backend != "huggingface":
        raise ValueError("api_key is required: specify it in config.toml or as an argument")

    merged_kwargs = {**config.extra, **kwargs}

    if config.reasoning_effort is not None and "reasoning_effort" not in merged_kwargs:
        reasoning = ReasoningEffort(effort=config.reasoning_effort.effort or "low", generate_summary=config.reasoning_effort.generate_summary, summary=config.reasoning_effort.summary)
        merged_kwargs["reasoning_effort"] = reasoning

    return await get_agent(backend=final_backend, model=final_model, api_key=final_api_key, base_url=final_base_url, **merged_kwargs)


def _load_config_from_path(config_path: Optional[Union[str, Path]], backend: Optional[str]) -> AgentConfig:
    """Load config from a specific path or use the default search.

    Args:
        config_path: Optional path to config file
        backend: Optional backend name for layered config

    Returns:
        AgentConfig with loaded values
    """
    if config_path is not None:
        return _load_from_specific_path(Path(config_path), backend)
    return load_agent_config(backend=backend)


def _load_from_specific_path(path: Path, backend: Optional[str]) -> AgentConfig:
    """Load config from a specific path.

    Args:
        path: Path to the TOML file
        backend: Optional backend name for layered config

    Returns:
        AgentConfig with loaded values
    """
    import tomllib as _toml

    from .config import AgentConfig
    from .config import _merge_configs
    from .config import _parse_agent_section

    if not path.exists():
        return AgentConfig()

    try:
        with path.open("rb") as f:
            data = _toml.load(f)
    except Exception:
        return AgentConfig()

    section = data.get("midori_ai_agent_base")

    if section is None or not isinstance(section, dict):
        return AgentConfig()

    base_config = _parse_agent_section(section)

    if backend is None:
        return base_config

    backend_section = section.get(backend)

    if backend_section is None or not isinstance(backend_section, dict):
        return base_config

    backend_config = _parse_agent_section(backend_section)

    return _merge_configs(base_config, backend_config)
