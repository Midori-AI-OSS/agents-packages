"""Configuration for HuggingFace local agent."""

from dataclasses import dataclass
from dataclasses import field

from typing import Any
from typing import Literal


DeviceType = Literal["auto", "cpu", "cuda", "mps"]


@dataclass
class HuggingFaceConfig:
    """Configuration for HuggingFace local inference.

    Attributes:
        model: HuggingFace model identifier (e.g., 'TinyLlama/TinyLlama-1.1B-Chat-v1.0').
        device: Device to run inference on ('auto', 'cpu', 'cuda', 'mps').
        torch_dtype: Data type for model weights ('auto', 'float16', 'float32', 'bfloat16').
        max_new_tokens: Maximum tokens to generate per response.
        temperature: Sampling temperature (0.0-2.0). Higher = more creative.
        top_p: Nucleus sampling probability (0.0-1.0).
        top_k: Top-k sampling parameter.
        do_sample: Whether to use sampling (True) or greedy decoding (False).
        context_window: Maximum context window size for the model.
        trust_remote_code: Whether to trust remote code in model files.
        load_in_8bit: Load model in 8-bit precision (requires bitsandbytes).
        load_in_4bit: Load model in 4-bit precision (requires bitsandbytes).
        extra: Additional generation kwargs passed to the model.
    """

    model: str
    device: DeviceType = "auto"
    torch_dtype: str = "auto"
    max_new_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    do_sample: bool = True
    context_window: int = 4096
    trust_remote_code: bool = False
    load_in_8bit: bool = False
    load_in_4bit: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


def create_config(model: str, device: DeviceType = "auto", torch_dtype: str = "auto", max_new_tokens: int = 512, temperature: float = 0.7, top_p: float = 0.9, top_k: int = 50, do_sample: bool = True, context_window: int = 4096, trust_remote_code: bool = False, load_in_8bit: bool = False, load_in_4bit: bool = False, **kwargs: Any) -> HuggingFaceConfig:
    """Create a HuggingFaceConfig from parameters.

    Args:
        model: HuggingFace model identifier.
        device: Device to run inference on.
        torch_dtype: Data type for model weights.
        max_new_tokens: Maximum tokens to generate.
        temperature: Sampling temperature.
        top_p: Nucleus sampling probability.
        top_k: Top-k sampling parameter.
        do_sample: Whether to use sampling.
        context_window: Maximum context window size.
        trust_remote_code: Whether to trust remote code.
        load_in_8bit: Load model in 8-bit precision.
        load_in_4bit: Load model in 4-bit precision.
        **kwargs: Additional generation kwargs.

    Returns:
        Configured HuggingFaceConfig instance.
    """
    return HuggingFaceConfig(model=model, device=device, torch_dtype=torch_dtype, max_new_tokens=max_new_tokens, temperature=temperature, top_p=top_p, top_k=top_k, do_sample=do_sample, context_window=context_window, trust_remote_code=trust_remote_code, load_in_8bit=load_in_8bit, load_in_4bit=load_in_4bit, extra=kwargs)
