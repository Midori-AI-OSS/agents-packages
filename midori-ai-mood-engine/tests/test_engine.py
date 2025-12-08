"""Tests for the main MoodEngine class."""

import pytest
import pytz

from datetime import datetime

from midori_ai_mood_engine import MoodEngine
from midori_ai_mood_engine import MealType
from midori_ai_mood_engine import StepType


@pytest.fixture
def engine():
    """Create a test engine instance."""
    tz = pytz.timezone("America/Los_Angeles")
    cycle_start = datetime(2008, 4, 15, 0, 0, 0, tzinfo=tz)
    return MoodEngine(cycle_start=cycle_start, step_type=StepType.DAY)


def test_engine_initialization(engine):
    """Test that the engine initializes correctly."""
    assert engine is not None
    assert engine.hormone_model is not None
    assert engine.loneliness_tracker is not None
    assert engine.energy_tracker is not None


def test_get_current_mood(engine):
    """Test getting the current mood state."""
    mood = engine.get_current_mood()
    assert mood is not None
    assert hasattr(mood, "energy")
    assert hasattr(mood, "happiness")
    assert hasattr(mood, "irritability")
    assert hasattr(mood, "anxiety")
    assert hasattr(mood, "loneliness")


def test_get_mood_at_datetime(engine):
    """Test getting mood at a specific datetime."""
    tz = pytz.timezone("America/Los_Angeles")
    test_time = datetime(2024, 6, 15, 12, 0, 0, tzinfo=tz)
    mood = engine.get_mood_at_datetime(test_time)
    assert mood is not None


def test_get_hormone_levels(engine):
    """Test getting hormone levels."""
    levels = engine.get_hormone_levels()
    assert isinstance(levels, dict)
    assert len(levels) > 20
    assert "Estradiol" in levels
    assert "Progesterone" in levels
    assert "Cortisol" in levels
    assert "Serotonin" in levels


def test_is_on_period(engine):
    """Test period detection."""
    is_period, intensity = engine.is_on_period()
    assert isinstance(is_period, bool)
    assert isinstance(intensity, float)
    assert 0.0 <= intensity <= 1.0


def test_apply_stress(engine):
    """Test applying stress impact."""
    _ = engine.get_current_mood()
    mood = engine.apply_stress(0.5)
    assert mood is not None
    assert hasattr(mood, "anxiety")


def test_apply_relaxation(engine):
    """Test applying relaxation impact."""
    _ = engine.get_current_mood()
    mood = engine.apply_relaxation(0.7)
    assert mood is not None


def test_apply_exercise(engine):
    """Test applying exercise impact."""
    initial_energy = engine.energy_tracker.current_energy
    _ = engine.get_current_mood()
    mood = engine.apply_exercise(intensity=0.6, duration_minutes=30)
    assert mood is not None
    assert engine.energy_tracker.current_energy < initial_energy


def test_apply_meal(engine):
    """Test applying meal impact."""
    _ = engine.get_current_mood()
    mood = engine.apply_meal(MealType.BREAKFAST)
    assert mood is not None


def test_apply_sleep_deprivation(engine):
    """Test applying sleep deprivation impact."""
    _ = engine.get_current_mood()
    mood = engine.apply_sleep_deprivation(hours=4)
    assert mood is not None


def test_apply_social_interaction(engine):
    """Test applying social interaction impact."""
    initial_interaction_count = len(engine.loneliness_tracker.interaction_history)
    _ = engine.get_current_mood()
    mood = engine.apply_social_interaction(quality=0.8, duration_minutes=30)
    assert mood is not None
    assert len(engine.loneliness_tracker.interaction_history) == initial_interaction_count + 1


def test_apply_rest(engine):
    """Test applying rest impact."""
    engine.energy_tracker.expend(50)
    initial_energy = engine.energy_tracker.current_energy
    _ = engine.get_current_mood()
    mood = engine.apply_rest(hours=2)
    assert mood is not None
    assert engine.energy_tracker.current_energy > initial_energy


def test_mood_state_to_dict(engine):
    """Test converting mood state to dictionary."""
    mood = engine.get_current_mood()
    mood_dict = mood.to_dict()
    assert isinstance(mood_dict, dict)
    assert "energy" in mood_dict
    assert "happiness" in mood_dict
    assert "loneliness" in mood_dict
