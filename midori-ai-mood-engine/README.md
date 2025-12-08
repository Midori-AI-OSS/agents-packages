# midori-ai-mood-engine

Comprehensive mood engine with hormone simulation, loneliness tracking, and energy modeling. Install directly from the repo using `git+`.

## Install from Git

### UV

Python Project Install
```bash
uv add "git+https://github.com/Midori-AI-OSS/agents-packages.git#subdirectory=midori-ai-mood-engine"
```

Temp Venv Install
```bash
uv pip install "git+https://github.com/Midori-AI-OSS/agents-packages.git#subdirectory=midori-ai-mood-engine"
```

### Pip

```bash
pip install "git+https://github.com/Midori-AI-OSS/agents-packages.git#subdirectory=midori-ai-mood-engine"
```

## Quick Start

```python
from midori_ai_mood_engine import MoodEngine, StepType
from datetime import datetime
import pytz

# Create engine
engine = MoodEngine(
    cycle_start=datetime(2008, 4, 15, tzinfo=pytz.timezone('America/Los_Angeles')),
    step_type=StepType.FULL
)

# Get current mood
mood = engine.get_current_mood()
print(f"Energy: {mood.energy:.2f}")
print(f"Happiness: {mood.happiness:.2f}")
print(f"Loneliness: {mood.loneliness:.2f}")

# Apply impacts
engine.apply_social_interaction(quality=0.8, duration_minutes=30)
engine.apply_stress(intensity=0.5)
engine.apply_rest(hours=8)
```

## Documentation

See [docs.md](docs.md) for detailed documentation.

## License

MIT
