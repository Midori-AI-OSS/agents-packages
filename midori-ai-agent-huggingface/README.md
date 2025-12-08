# midori-ai-agent-huggingface

Hugging Face local inference implementation of the Midori AI agent protocol. Enables fully local LLM inference without external servers.

## ⚠️ Important: Resource Requirements

This package runs LLM inference locally, which requires significant resources:

| Model Size | RAM Required | VRAM Required | Download Size |
|------------|--------------|---------------|---------------|
| 1B-3B      | ~4-6GB       | ~2-4GB        | ~1-5GB        |
| 7B         | ~14GB        | ~7GB          | ~7-14GB       |
| 13B        | ~26GB        | ~13GB         | ~13-26GB      |

**First inference will be slow** as the model downloads and loads. Subsequent calls are fast.

## Install from Git

### UV

Python Project Install:
```bash
uv add "git+https://github.com/Midori-AI-OSS/Carly-AGI#subdirectory=Rest-Servers/packages/midori-ai-agent-huggingface"
```

Temp Venv Install:
```bash
uv pip install "git+https://github.com/Midori-AI-OSS/Carly-AGI#subdirectory=Rest-Servers/packages/midori-ai-agent-huggingface"
```

### Pip

```bash
pip install "git+https://github.com/Midori-AI-OSS/Carly-AGI#subdirectory=Rest-Servers/packages/midori-ai-agent-huggingface"
```

### Optional Dependencies

For GPU support and quantization:
```bash
# PyTorch with CUDA (install separately based on your system)
pip install torch

# 8-bit/4-bit quantization
uv add "git+https://github.com/Midori-AI-OSS/Carly-AGI#subdirectory=Rest-Servers/packages/midori-ai-agent-huggingface[quantization]"
```

See [docs.md](docs.md) for detailed usage documentation.
