"""Tests for the hormone simulation subsystem."""

import pytest
import pytz

from datetime import datetime

from midori_ai_mood_engine import StepType
from midori_ai_mood_engine.hormones import HormoneCycleModel


@pytest.fixture
def model():
    """Create a test hormone model."""
    tz = pytz.timezone("America/Los_Angeles")
    cycle_start = datetime(2008, 4, 15, 0, 0, 0, tzinfo=tz)
    return HormoneCycleModel(cycle_start=cycle_start, step_type=StepType.DAY)


def test_model_initialization(model):
    """Test model initialization."""
    assert model is not None
    assert model.num_steps == 28


def test_forward_returns_hormones(model):
    """Test that forward returns hormone levels."""
    levels = model.forward(0)
    assert isinstance(levels, dict)
    assert len(levels) >= 20


def test_hormone_categories_present(model):
    """Test that all hormone categories are represented."""
    levels = model.forward(0)
    reproductive = ["GnRH", "FSH", "LH", "Estradiol", "Progesterone"]
    stress = ["Cortisol", "Adrenaline"]
    mood = ["Serotonin", "Dopamine", "Oxytocin", "Melatonin"]
    metabolism = ["Insulin", "Leptin", "Ghrelin"]
    for hormone in reproductive + stress + mood + metabolism:
        assert hormone in levels, f"Missing hormone: {hormone}"


def test_get_levels_at_datetime(model):
    """Test getting levels at a specific datetime."""
    tz = pytz.timezone("America/Los_Angeles")
    test_time = datetime(2024, 6, 15, 12, 0, 0, tzinfo=tz)
    levels = model.get_levels_at_datetime(test_time)
    assert isinstance(levels, dict)
    assert "Estradiol" in levels


def test_get_mood_mods(model):
    """Test getting mood modifiers."""
    mods = model.get_mood_mods(0)
    assert isinstance(mods, dict)
    expected_keys = ["energy", "irritability", "mood_swings", "happiness", "anxiety", "focus", "libido", "sleep_quality"]
    for key in expected_keys:
        assert key in mods, f"Missing mood modifier: {key}"


def test_get_mood_at_datetime(model):
    """Test getting mood at a specific datetime."""
    tz = pytz.timezone("America/Los_Angeles")
    test_time = datetime(2024, 6, 15, 12, 0, 0, tzinfo=tz)
    mods = model.get_mood_at_datetime(test_time)
    assert isinstance(mods, dict)


def test_is_on_period(model):
    """Test period detection."""
    tz = pytz.timezone("America/Los_Angeles")
    test_time = datetime(2024, 6, 15, 12, 0, 0, tzinfo=tz)
    is_period, intensity = model.is_on_period(test_time)
    assert isinstance(is_period, bool)
    assert isinstance(intensity, float)
    assert 0.0 <= intensity <= 1.0


def test_step_types():
    """Test different step types."""
    tz = pytz.timezone("America/Los_Angeles")
    cycle_start = datetime(2008, 4, 15, 0, 0, 0, tzinfo=tz)
    day_model = HormoneCycleModel(cycle_start=cycle_start, step_type=StepType.DAY)
    pulse_model = HormoneCycleModel(cycle_start=cycle_start, step_type=StepType.PULSE)
    full_model = HormoneCycleModel(cycle_start=cycle_start, step_type=StepType.FULL)
    assert day_model.num_steps == 28
    assert pulse_model.num_steps == 28 * 16
    assert full_model.num_steps == 28 * 24 * 60 * 2


def test_hormone_values_are_positive(model):
    """Test that hormone values are generally positive."""
    for step in range(28):
        levels = model.forward(step)
        for hormone, value in levels.items():
            val = value.item()
            assert val > -50, f"{hormone} at step {step} has unreasonably low value: {val}"
