"""Main MoodEngine class - unified interface for mood simulation."""

import pytz

from datetime import datetime
from typing import Any

from .config import MoodEngineConfig
from .config import DEFAULT_CYCLE_START
from .enums import MealType
from .enums import StepType
from .profile import MoodProfile
from .profile import MoodState
from .hormones import HormoneCycleModel
from .loneliness import LonelinessTracker
from .loneliness import SocialNeedModel
from .loneliness import calculate_loneliness_influence
from .loneliness import calculate_interaction_satisfaction
from .energy import EnergyTracker
from .energy import get_circadian_modifier
from .energy import calculate_exercise_expenditure
from .energy import calculate_rest_recovery
from .mood_modifiers import calculate_unified_mood
from .mood_modifiers import apply_impact_to_mood
from .impact import apply_stress as _apply_stress
from .impact import apply_relaxation as _apply_relaxation
from .impact import apply_exercise as _apply_exercise
from .impact import apply_meal as _apply_meal
from .impact import apply_sleep_deprivation as _apply_sleep_deprivation
from .impact import apply_social_interaction as _apply_social_interaction
from .impact import apply_rest as _apply_rest
from .training import MoodTrainer
from .persistence import save_model as _save_model
from .persistence import load_model as _load_model


class MoodEngine:
    """Main mood engine with hormone simulation, loneliness tracking, and energy modeling."""

    def __init__(self, cycle_start: datetime | None = None, step_type: StepType = StepType.FULL, config: MoodEngineConfig | None = None, timezone: str = "America/Los_Angeles"):
        """Initialize the mood engine."""
        self.timezone = pytz.timezone(timezone)

        if config is not None:
            self.config = config
            self.profile = MoodProfile(gender=config.profile.gender, age=config.profile.age, modifier=config.profile.modifier, cycle_enabled=config.profile.cycle_enabled, loneliness_enabled=config.profile.loneliness_enabled, energy_enabled=config.profile.energy_enabled)
            cycle_start = config.cycle_start
            step_type = config.default_step_type
        else:
            self.config = None
            self.profile = MoodProfile()

        if cycle_start is None:
            cycle_start = DEFAULT_CYCLE_START

        self.cycle_start = cycle_start
        self.step_type = step_type
        self.hormone_model = HormoneCycleModel(cycle_start=cycle_start, step_type=step_type)
        self.loneliness_tracker = LonelinessTracker()
        self.social_need = SocialNeedModel()
        self.energy_tracker = EnergyTracker()
        self.trainer: MoodTrainer | None = None
        self._current_mood: MoodState | None = None

    def get_mood_at_datetime(self, current_time: datetime) -> MoodState:
        """Get unified mood state at a specific datetime."""
        hormone_mods = {}
        if self.profile.cycle_enabled:
            hormone_mods = self.hormone_model.get_mood_at_datetime(current_time)

        loneliness_influence = {}
        if self.profile.loneliness_enabled:
            hours_since = self.loneliness_tracker.get_hours_since_interaction(current_time)
            recent_quality = self.loneliness_tracker.get_recent_interaction_quality(current_time=current_time)
            loneliness_influence = calculate_loneliness_influence(hours_since_interaction=hours_since, social_need=self.social_need.get_urgency(), interaction_quality=recent_quality)

        energy_level = 0.5
        if self.profile.energy_enabled:
            self.energy_tracker.update(current_time)
            energy_level = self.energy_tracker.get_level()

        circadian_mod = get_circadian_modifier(current_time)

        self._current_mood = calculate_unified_mood(hormone_mods=hormone_mods, loneliness_influence=loneliness_influence, energy_level=energy_level, circadian_modifier=circadian_mod, profile_modifier=self.profile.modifier)

        return self._current_mood

    def get_current_mood(self) -> MoodState:
        """Get current mood state at the current time."""
        current_time = datetime.now(self.timezone)
        return self.get_mood_at_datetime(current_time)

    def get_hormone_levels(self, current_time: datetime | None = None) -> dict[str, float]:
        """Get current hormone levels."""
        if current_time is None:
            current_time = datetime.now(self.timezone)

        levels = self.hormone_model.get_levels_at_datetime(current_time)
        return {name: tensor.item() for name, tensor in levels.items()}

    def is_on_period(self, current_time: datetime | None = None) -> tuple[bool, float]:
        """Check if currently on menstrual period."""
        if current_time is None:
            current_time = datetime.now(self.timezone)

        return self.hormone_model.is_on_period(current_time)

    def apply_stress(self, intensity: float) -> MoodState:
        """Apply stress impact to current mood."""
        impact = _apply_stress(intensity)
        if self._current_mood is None:
            self._current_mood = self.get_current_mood()
        self._current_mood = apply_impact_to_mood(self._current_mood, impact)
        return self._current_mood

    def apply_relaxation(self, intensity: float) -> MoodState:
        """Apply relaxation impact to current mood."""
        impact = _apply_relaxation(intensity)
        if self._current_mood is None:
            self._current_mood = self.get_current_mood()
        self._current_mood = apply_impact_to_mood(self._current_mood, impact)
        return self._current_mood

    def apply_exercise(self, intensity: float, duration_minutes: float) -> MoodState:
        """Apply exercise impact to current mood and energy."""
        impact = _apply_exercise(intensity, duration_minutes)
        if self._current_mood is None:
            self._current_mood = self.get_current_mood()
        self._current_mood = apply_impact_to_mood(self._current_mood, impact)
        expenditure = calculate_exercise_expenditure(intensity, duration_minutes)
        self.energy_tracker.expend(expenditure)
        return self._current_mood

    def apply_meal(self, meal_type: MealType) -> MoodState:
        """Apply meal impact to current mood."""
        impact = _apply_meal(meal_type)
        if self._current_mood is None:
            self._current_mood = self.get_current_mood()
        self._current_mood = apply_impact_to_mood(self._current_mood, impact)
        return self._current_mood

    def apply_sleep_deprivation(self, hours: float) -> MoodState:
        """Apply sleep deprivation impact to current mood."""
        impact = _apply_sleep_deprivation(hours)
        if self._current_mood is None:
            self._current_mood = self.get_current_mood()
        self._current_mood = apply_impact_to_mood(self._current_mood, impact)
        return self._current_mood

    def apply_social_interaction(self, quality: float, duration_minutes: float) -> MoodState:
        """Apply social interaction impact to current mood and loneliness."""
        impact = _apply_social_interaction(quality, duration_minutes)
        if self._current_mood is None:
            self._current_mood = self.get_current_mood()
        self._current_mood = apply_impact_to_mood(self._current_mood, impact)
        self.loneliness_tracker.record_interaction(quality=quality, duration_minutes=duration_minutes)
        satisfaction = calculate_interaction_satisfaction(quality, duration_minutes)
        self.social_need.satisfy(satisfaction)
        return self._current_mood

    def apply_rest(self, hours: float) -> MoodState:
        """Apply rest impact to current mood and energy."""
        impact = _apply_rest(hours)
        if self._current_mood is None:
            self._current_mood = self.get_current_mood()
        self._current_mood = apply_impact_to_mood(self._current_mood, impact)
        recovery = calculate_rest_recovery(hours)
        self.energy_tracker.recover(recovery)
        return self._current_mood

    def retrain(self, feedback_data: list[dict[str, Any]] | None = None) -> dict[str, float]:
        """Retrain the model with feedback data."""
        if self.trainer is None:
            self.trainer = MoodTrainer(self.hormone_model)

        if feedback_data is not None:
            from .training import FeedbackSample

            samples = [FeedbackSample(predicted=f["predicted"], actual=f["actual"], context=f.get("context")) for f in feedback_data]
            return self.trainer.retrain(feedback_data=samples)

        return self.trainer.retrain()

    async def save_model(self, path: str, metadata: dict[str, Any] | None = None) -> None:
        """Save the hormone model to disk with encryption (async, non-blocking)."""
        await _save_model(self.hormone_model, path, metadata)

    async def load_model(self, path: str) -> dict[str, Any]:
        """Load the hormone model from disk with decryption (async, non-blocking)."""
        return await _load_model(self.hormone_model, path)

    @classmethod
    async def from_model_file(cls, path: str, **kwargs) -> "MoodEngine":
        """Create a MoodEngine from a saved model file (async, non-blocking)."""
        engine = cls(**kwargs)
        await engine.load_model(path)
        return engine
