# Midori AI Mood Engine - Documentation

Comprehensive mood management system with hormone simulation, loneliness tracking, energy modeling, and PyTorch-based self-retraining.

## Features

- **Hormone Simulation**: 28+ hormones across reproductive, stress, mood, and metabolism categories with 28-day cycle support
- **Loneliness Tracking**: Time-since-interaction tracking, social need accumulation, connection quality scoring
- **Energy Modeling**: Base energy tracking, activity expenditure, rest recovery, circadian rhythm integration
- **Unified Mood API**: Single interface returning energy, happiness, irritability, anxiety, focus, loneliness, etc.
- **Self-Retraining**: PyTorch model learns from feedback, adjusts response curves based on observed mood outcomes
- **Profile Configuration**: Gender, age, modifier intensity, feature toggles

## Installation

```bash
uv add midori-ai-mood-engine
```

## Core Concepts

### MoodEngine

The main entry point for the mood system. It combines all subsystems into a unified interface.

```python
from midori_ai_mood_engine import MoodEngine, StepType
from datetime import datetime
import pytz

tz = pytz.timezone('America/Los_Angeles')
engine = MoodEngine(
    cycle_start=datetime(2008, 4, 15, tzinfo=tz),
    step_type=StepType.FULL
)
```

### Resolution Modes (StepType)

- `StepType.DAY`: 28 daily steps (fastest, least precise)
- `StepType.PULSE`: 448 steps (90-minute pulses over 28 days)
- `StepType.FULL`: 80,640 steps (30-second intervals, most precise)

### MoodState

Represents a snapshot of the current mood with these attributes:
- `energy`: Physical and mental energy level
- `happiness`: General sense of well-being
- `irritability`: Tendency to react negatively
- `anxiety`: Nervousness and worry
- `focus`: Ability to concentrate
- `loneliness`: Sense of social isolation
- `mood_swings`: Volatility of emotional state
- `libido`: Sexual drive
- `sleep_quality`: Quality of recent sleep
- `social_need`: Desire for social interaction

## Impact System API

Apply external events that affect mood state:

### `apply_stress(intensity: float) -> MoodState`
Apply stress impact. Raises cortisol and adrenaline effects.
- `intensity`: 0.0 to 1.0

### `apply_relaxation(intensity: float) -> MoodState`
Apply relaxation impact. Raises oxytocin and serotonin effects.
- `intensity`: 0.0 to 1.0

### `apply_exercise(intensity: float, duration_minutes: float) -> MoodState`
Apply exercise impact. Raises endorphins, testosterone, depletes energy.
- `intensity`: 0.0 to 1.0
- `duration_minutes`: Duration of exercise

### `apply_meal(meal_type: MealType) -> MoodState`
Apply meal impact. Affects insulin, leptin, ghrelin.
- `meal_type`: `MealType.BREAKFAST`, `LUNCH`, `DINNER`, `SNACK`, `HEAVY`, `LIGHT`

### `apply_sleep_deprivation(hours: float) -> MoodState`
Apply sleep deprivation impact.
- `hours`: Hours of sleep missed

### `apply_social_interaction(quality: float, duration_minutes: float) -> MoodState`
Apply social interaction impact. Reduces loneliness, raises oxytocin.
- `quality`: 0.0 to 1.0 (quality of interaction)
- `duration_minutes`: Duration of interaction

### `apply_rest(hours: float) -> MoodState`
Apply rest impact. Restores energy, balances hormones.
- `hours`: Hours of rest

## Self-Retraining System

The engine can learn from feedback to adjust its response curves:

```python
# Collect feedback
feedback = [
    {"predicted": {"happiness": 0.7}, "actual": {"happiness": 0.5}},
    {"predicted": {"energy": 0.6}, "actual": {"energy": 0.8}},
]

# Retrain model
result = engine.retrain(feedback)
print(f"Retrained with {result['samples']} samples, final loss: {result['final_loss']:.4f}")

# Save model (async, encrypted with system-derived key - 12 iterations)
await engine.save_model("mood_engine.pt")

# Load model (async, decrypted with system-derived key)
await engine.load_model("mood_engine.pt")
```

**Security Note**: Model persistence uses the `midori-ai-media-vault` encryption system with 12 iterations of system-stats-derived key hashing. This ensures models are encrypted at rest using system-specific keys.

## Profile Configuration

Configure the engine for different profiles:

```python
from midori_ai_mood_engine import MoodProfile, Gender

profile = MoodProfile(
    gender=Gender.FEMALE,      # FEMALE, MALE, or CUSTOM
    age=25,                    # Affects baseline hormone levels
    modifier=1.0,              # Global intensity multiplier
    cycle_enabled=True,        # Enable menstrual cycle
    loneliness_enabled=True,   # Enable loneliness tracking
    energy_enabled=True        # Enable energy simulation
)
```

## TOML Configuration

```toml
[mood_engine]
cycle_start = "2008-04-15T00:00:00"
timezone = "America/Los_Angeles"
default_step_type = "full"

[mood_engine.profile]
gender = "female"
age = 25
modifier = 1.0
cycle_enabled = true
loneliness_enabled = true
energy_enabled = true

[mood_engine.training]
auto_retrain = true
retrain_interval_hours = 24
min_feedback_samples = 100
```

Load configuration:

```python
from midori_ai_mood_engine import MoodEngine, load_config_from_toml

config = load_config_from_toml("config.toml")
engine = MoodEngine(config=config)
```

## Hormone Categories

### Reproductive (14 hormones)
- GnRH, FSH, LH, Estradiol, Progesterone
- Inhibin A, Inhibin B, Activin, AMH
- Prolactin, hCG, Relaxin, Testosterone, DHEA

### Stress (3 hormones)
- Cortisol, Adrenaline, Norepinephrine

### Mood (6 hormones)
- Melatonin, Serotonin, Dopamine
- Oxytocin, GABA, Endorphins

### Metabolism (5 hormones)
- Insulin, Leptin, Ghrelin, T3, T4

## API Reference

### MoodEngine

```python
class MoodEngine:
    def get_mood_at_datetime(current_time: datetime) -> MoodState
    def get_current_mood() -> MoodState
    def get_hormone_levels(current_time: datetime = None) -> dict[str, float]
    def is_on_period(current_time: datetime = None) -> tuple[bool, float]
    def apply_stress(intensity: float) -> MoodState
    def apply_relaxation(intensity: float) -> MoodState
    def apply_exercise(intensity: float, duration_minutes: float) -> MoodState
    def apply_meal(meal_type: MealType) -> MoodState
    def apply_sleep_deprivation(hours: float) -> MoodState
    def apply_social_interaction(quality: float, duration_minutes: float) -> MoodState
    def apply_rest(hours: float) -> MoodState
    def retrain(feedback_data: list[dict] = None) -> dict[str, float]
    async def save_model(path: str, metadata: dict = None) -> None
    async def load_model(path: str) -> dict[str, Any]
```

## Notes

- The hardcoded cycle start date (2008-04-15) is a specific reference point for backward compatibility
- PyTorch is required for self-retraining capability
- All persistence methods (save_model, load_model) are async and non-blocking
- Model files are encrypted using system-stats-derived keys (12 iterations) via midori-ai-media-vault
- Energy subsystem uses circadian rhythm for realistic energy patterns
