"""Configuration management for the mood engine package."""

import os
import tomllib

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from typing import Any

import pytz

from .enums import Gender
from .enums import StepType


DEFAULT_CYCLE_START = datetime(2008, 4, 15, 0, 0, 0, tzinfo=pytz.timezone("America/Los_Angeles"))
DEFAULT_TIMEZONE = "America/Los_Angeles"
DEFAULT_STEP_TYPE = StepType.FULL


@dataclass
class ProfileConfig:
    """Profile configuration for the mood engine."""
    gender: Gender = Gender.FEMALE
    age: int = 25
    modifier: float = 1.0
    cycle_enabled: bool = True
    loneliness_enabled: bool = True
    energy_enabled: bool = True


@dataclass
class TrainingConfig:
    """Training configuration for self-retraining system."""
    auto_retrain: bool = True
    retrain_interval_hours: int = 24
    min_feedback_samples: int = 100


@dataclass
class MoodEngineConfig:
    """Main configuration for the mood engine."""
    cycle_start: datetime = field(default_factory=lambda: DEFAULT_CYCLE_START)
    timezone: str = DEFAULT_TIMEZONE
    default_step_type: StepType = DEFAULT_STEP_TYPE
    profile: ProfileConfig = field(default_factory=ProfileConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)


def load_config_from_toml(path: str) -> MoodEngineConfig:
    """Load configuration from a TOML file."""
    if not os.path.exists(path):
        return MoodEngineConfig()

    with open(path, "rb") as f:
        data = tomllib.load(f)

    return _parse_config_dict(data)


def _parse_config_dict(data: dict[str, Any]) -> MoodEngineConfig:
    """Parse a configuration dictionary into a MoodEngineConfig object."""
    mood_engine_data = data.get("mood_engine", {})

    config = MoodEngineConfig()

    if "cycle_start" in mood_engine_data:
        tz = pytz.timezone(mood_engine_data.get("timezone", DEFAULT_TIMEZONE))
        config.cycle_start = datetime.fromisoformat(mood_engine_data["cycle_start"]).replace(tzinfo=tz)

    if "timezone" in mood_engine_data:
        config.timezone = mood_engine_data["timezone"]

    if "default_step_type" in mood_engine_data:
        config.default_step_type = StepType(mood_engine_data["default_step_type"])

    profile_data = mood_engine_data.get("profile", {})
    if profile_data:
        config.profile = ProfileConfig(gender=Gender(profile_data.get("gender", "female")), age=profile_data.get("age", 25), modifier=profile_data.get("modifier", 1.0), cycle_enabled=profile_data.get("cycle_enabled", True), loneliness_enabled=profile_data.get("loneliness_enabled", True), energy_enabled=profile_data.get("energy_enabled", True))

    training_data = mood_engine_data.get("training", {})
    if training_data:
        config.training = TrainingConfig(auto_retrain=training_data.get("auto_retrain", True), retrain_interval_hours=training_data.get("retrain_interval_hours", 24), min_feedback_samples=training_data.get("min_feedback_samples", 100))

    return config
