"""Pipeline lifecycle management for HuggingFace models."""

import asyncio

from typing import Any
from typing import Optional

from midori_ai_logger import MidoriAiLogger

from .config import HuggingFaceConfig


class PipelineManager:
    """Manages HuggingFace pipeline lifecycle with lazy loading.

    This class handles:
    - Lazy model loading (load on first request)
    - Device selection and memory management
    - Pipeline configuration and generation kwargs
    - Response parsing for reasoning models
    - Thread-safe loading/unloading with reference counting
    """

    def __init__(self, config: HuggingFaceConfig) -> None:
        """Initialize the pipeline manager.

        Args:
            config: HuggingFace configuration.
        """
        self._config = config
        self._pipeline: Optional[Any] = None
        self._tokenizer: Optional[Any] = None
        self._model: Optional[Any] = None
        self._logger = MidoriAiLogger(None, name="PipelineManager")
        self._lock = asyncio.Lock()
        self._ref_count = 0

    @property
    def is_loaded(self) -> bool:
        """Check if the model pipeline is loaded."""
        return self._pipeline is not None

    @property
    def tokenizer(self) -> Optional[Any]:
        """Get the tokenizer if pipeline is loaded."""
        if self._pipeline is not None:
            return self._pipeline.tokenizer
        return None

    def _get_torch_dtype(self) -> Any:
        """Get the torch dtype from config string.

        Returns:
            torch dtype or "auto".
        """
        import torch

        dtype_map = {"float16": torch.float16, "float32": torch.float32, "bfloat16": torch.bfloat16, "auto": "auto"}
        return dtype_map.get(self._config.torch_dtype, "auto")

    def _get_device(self) -> str:
        """Resolve the device to use.

        Returns:
            Device string for pipeline.
        """
        if self._config.device != "auto":
            return self._config.device

        try:
            import torch

            if torch.cuda.is_available():
                return "cuda"
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass

        return "cpu"

    async def load_pipeline(self) -> Any:
        """Load the HuggingFace text generation pipeline with thread-safe locking.

        Uses reference counting to allow multiple concurrent users while preventing
        redundant loads.

        Returns:
            Configured pipeline ready for inference.
        """
        async with self._lock:
            self._ref_count += 1
            if self._pipeline is not None:
                return self._pipeline

            import transformers

            device = self._get_device()
            torch_dtype = self._get_torch_dtype()

            model_kwargs: dict[str, Any] = {"trust_remote_code": self._config.trust_remote_code}

            if torch_dtype != "auto":
                model_kwargs["torch_dtype"] = torch_dtype

            if self._config.load_in_8bit:
                model_kwargs["load_in_8bit"] = True
            elif self._config.load_in_4bit:
                model_kwargs["load_in_4bit"] = True

            self._pipeline = transformers.pipeline("text-generation", model=self._config.model, device_map=device if device != "cpu" else None, device=None if device != "cpu" else device, model_kwargs=model_kwargs if model_kwargs else None, trust_remote_code=self._config.trust_remote_code)

            return self._pipeline

    def get_generation_kwargs(self) -> dict[str, Any]:
        """Get generation kwargs for inference.

        Returns:
            Dictionary of generation parameters.
        """
        kwargs: dict[str, Any] = {"max_new_tokens": self._config.max_new_tokens, "temperature": self._config.temperature, "top_p": self._config.top_p, "top_k": self._config.top_k, "do_sample": self._config.do_sample, "return_full_text": False}

        kwargs.update(self._config.extra)

        return kwargs

    def parse_response(self, text: str) -> Optional[dict[str, Any]]:
        """Parse model response using tokenizer's parse_response if available.

        Uses HuggingFace's tokenizer.parse_response() method for models that support it.
        This enables proper parsing of reasoning/thinking content for models like
        DeepSeek-R1, GPT-OSS, and other reasoning models.

        See: https://huggingface.co/docs/transformers/main/chat_response_parsing

        Args:
            text: Raw model output text.

        Returns:
            Parsed response dict with 'thinking' and 'content' keys if supported,
            None if tokenizer doesn't support parse_response.
        """
        tokenizer = self.tokenizer
        if tokenizer is None:
            return None

        if not hasattr(tokenizer, "parse_response"):
            return None

        try:
            return tokenizer.parse_response(text)
        except Exception:
            return None

    def generate(self, prompt: str, stream: bool = False) -> str:
        """Generate text using the pipeline.

        Args:
            prompt: Input prompt for generation.
            stream: Whether to use streaming (for async streaming only).

        Returns:
            Generated text response.
        """
        if self._pipeline is None:
            raise RuntimeError("Pipeline not loaded. Call load_pipeline() first.")

        gen_kwargs = self.get_generation_kwargs()

        outputs = self._pipeline(prompt, **gen_kwargs)

        if outputs and len(outputs) > 0:
            result = outputs[0]
            if isinstance(result, dict) and "generated_text" in result:
                return str(result["generated_text"])
            return str(result)

        return ""

    def create_streamer(self) -> Any:
        """Create a TextIteratorStreamer for streaming generation.

        Returns:
            TextIteratorStreamer instance for the current pipeline.

        Raises:
            RuntimeError: If pipeline is not loaded.
        """
        if self._pipeline is None:
            raise RuntimeError("Pipeline not loaded. Call load_pipeline() first.")

        from transformers import TextIteratorStreamer

        return TextIteratorStreamer(self._pipeline.tokenizer, skip_prompt=True, skip_special_tokens=True)

    async def unload(self) -> None:
        """Unload the pipeline and free memory with reference counting.

        Only unloads when reference count reaches zero.
        """
        async with self._lock:
            self._ref_count = max(0, self._ref_count - 1)
            if self._ref_count > 0:
                return

            if self._pipeline is not None:
                del self._pipeline
                self._pipeline = None

            if self._model is not None:
                del self._model
                self._model = None

            if self._tokenizer is not None:
                del self._tokenizer
                self._tokenizer = None

            try:
                import torch

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass
