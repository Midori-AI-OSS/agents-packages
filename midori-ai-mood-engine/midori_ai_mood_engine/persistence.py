"""Model persistence for save/load functionality with encryption."""

import io
import os
import json
import asyncio

import torch

from torch import nn

from dataclasses import asdict
from datetime import datetime
from typing import Any

from midori_ai_media_vault.system_crypto import SystemCrypto


CRYPTO_ITERATIONS = 12


async def save_model(model: nn.Module, path: str, metadata: dict[str, Any] | None = None) -> None:
    """Save a PyTorch model to disk with encryption and optional metadata."""
    state = {}
    state["model_state_dict"] = model.state_dict()
    state["metadata"] = metadata or {}
    state["saved_at"] = datetime.now().isoformat()

    buffer = io.BytesIO()
    torch.save(state, buffer)
    raw_bytes = buffer.getvalue()

    crypto = SystemCrypto(iterations=CRYPTO_ITERATIONS)
    encrypted_bytes = await asyncio.to_thread(crypto.encrypt, raw_bytes)

    await asyncio.to_thread(_write_bytes, path, encrypted_bytes)


async def load_model(model: nn.Module, path: str) -> dict[str, Any]:
    """Load a PyTorch model from disk with decryption and return metadata."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model file not found: {path}")

    encrypted_bytes = await asyncio.to_thread(_read_bytes, path)

    crypto = SystemCrypto(iterations=CRYPTO_ITERATIONS)
    raw_bytes = await asyncio.to_thread(crypto.decrypt, encrypted_bytes)

    buffer = io.BytesIO(raw_bytes)
    state = torch.load(buffer, weights_only=False)
    model.load_state_dict(state["model_state_dict"])

    result: dict[str, Any] = {}
    result["metadata"] = state.get("metadata", {})
    result["saved_at"] = state.get("saved_at")

    return result


async def save_engine_state(engine_state: dict[str, Any], path: str) -> None:
    """Save the complete engine state to disk with encryption."""
    serializable_state = _make_serializable(engine_state)
    json_bytes = json.dumps(serializable_state, indent=2).encode("utf-8")

    crypto = SystemCrypto(iterations=CRYPTO_ITERATIONS)
    encrypted_bytes = await asyncio.to_thread(crypto.encrypt, json_bytes)

    await asyncio.to_thread(_write_bytes, path, encrypted_bytes)


async def load_engine_state(path: str) -> dict[str, Any]:
    """Load the complete engine state from disk with decryption."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"State file not found: {path}")

    encrypted_bytes = await asyncio.to_thread(_read_bytes, path)

    crypto = SystemCrypto(iterations=CRYPTO_ITERATIONS)
    json_bytes = await asyncio.to_thread(crypto.decrypt, encrypted_bytes)

    return json.loads(json_bytes.decode("utf-8"))


def _write_bytes(path: str, data: bytes) -> None:
    """Write bytes to file."""
    with open(path, "wb") as f:
        f.write(data)


def _read_bytes(path: str) -> bytes:
    """Read bytes from file."""
    with open(path, "rb") as f:
        return f.read()


def _make_serializable(obj: Any) -> Any:
    """Convert an object to a JSON-serializable format."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_make_serializable(item) for item in obj]
    elif hasattr(obj, "__dataclass_fields__"):
        return _make_serializable(asdict(obj))
    elif hasattr(obj, "value"):
        return obj.value
    else:
        return obj
