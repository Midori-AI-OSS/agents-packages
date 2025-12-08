"""Tests for the energy simulation subsystem."""

import pytest

from datetime import datetime
from datetime import timedelta

from midori_ai_mood_engine.energy import EnergyTracker
from midori_ai_mood_engine.energy import calculate_exercise_expenditure
from midori_ai_mood_engine.energy import calculate_mental_work_expenditure
from midori_ai_mood_engine.energy import calculate_stress_expenditure
from midori_ai_mood_engine.energy import calculate_social_expenditure
from midori_ai_mood_engine.energy import calculate_sleep_recovery
from midori_ai_mood_engine.energy import calculate_rest_recovery
from midori_ai_mood_engine.energy import calculate_nap_recovery
from midori_ai_mood_engine.energy import calculate_meal_recovery
from midori_ai_mood_engine.energy import get_circadian_modifier
from midori_ai_mood_engine.energy import get_alertness_level
from midori_ai_mood_engine.energy import is_optimal_sleep_time
from midori_ai_mood_engine.energy import get_recommended_wake_time


@pytest.fixture
def tracker():
    """Create a test energy tracker."""
    return EnergyTracker()


class TestEnergyTracker:
    """Tests for EnergyTracker."""

    def test_initialization(self, tracker):
        """Test tracker initialization."""
        assert tracker.current_energy == 100.0
        assert tracker.max_energy == 100.0

    def test_expend(self, tracker):
        """Test energy expenditure."""
        tracker.expend(30)
        assert tracker.current_energy == 70.0

    def test_expend_floor(self, tracker):
        """Test that energy doesn't go below min."""
        tracker.expend(150)
        assert tracker.current_energy == 0.0

    def test_recover(self, tracker):
        """Test energy recovery."""
        tracker.expend(50)
        tracker.recover(20)
        assert tracker.current_energy == 70.0

    def test_recover_ceiling(self, tracker):
        """Test that energy doesn't exceed max."""
        tracker.recover(50)
        assert tracker.current_energy == 100.0

    def test_get_level(self, tracker):
        """Test getting energy level as percentage."""
        tracker.current_energy = 50
        assert tracker.get_level() == 0.5

    def test_get_fatigue_level(self, tracker):
        """Test getting fatigue level."""
        tracker.current_energy = 30
        assert tracker.get_fatigue_level() == 0.7

    def test_reset(self, tracker):
        """Test resetting energy."""
        tracker.expend(50)
        tracker.reset()
        assert tracker.current_energy == 100.0

    def test_update_with_passive_drain(self, tracker):
        """Test passive energy drain over time."""
        now = datetime.now()
        tracker.update(now)
        later = now + timedelta(hours=2)
        tracker.update(later)
        expected_drain = tracker.passive_drain_rate * 2
        assert tracker.current_energy == 100.0 - expected_drain


class TestExpenditureFunctions:
    """Tests for expenditure calculation functions."""

    def test_exercise_expenditure(self):
        """Test exercise expenditure calculation."""
        expend = calculate_exercise_expenditure(intensity=0.5, duration_minutes=30)
        assert expend > 0

    def test_exercise_intensity_effect(self):
        """Test that higher intensity costs more energy."""
        low = calculate_exercise_expenditure(0.2, 30)
        high = calculate_exercise_expenditure(0.8, 30)
        assert high > low

    def test_mental_work_expenditure(self):
        """Test mental work expenditure calculation."""
        expend = calculate_mental_work_expenditure(intensity=0.7, duration_minutes=60)
        assert expend > 0

    def test_stress_expenditure(self):
        """Test stress expenditure calculation."""
        expend = calculate_stress_expenditure(intensity=0.8, duration_minutes=30)
        assert expend > 0

    def test_social_expenditure(self):
        """Test social expenditure calculation."""
        expend = calculate_social_expenditure(intensity=0.5, duration_minutes=60)
        assert expend > 0


class TestRecoveryFunctions:
    """Tests for recovery calculation functions."""

    def test_sleep_recovery(self):
        """Test sleep recovery calculation."""
        recovery = calculate_sleep_recovery(hours=8, quality=1.0)
        assert recovery > 0

    def test_sleep_quality_effect(self):
        """Test that sleep quality affects recovery."""
        good = calculate_sleep_recovery(8, quality=1.0)
        poor = calculate_sleep_recovery(8, quality=0.5)
        assert good > poor

    def test_rest_recovery(self):
        """Test rest recovery calculation."""
        recovery = calculate_rest_recovery(hours=2)
        assert recovery == 10.0

    def test_nap_recovery(self):
        """Test nap recovery calculation."""
        short_nap = calculate_nap_recovery(minutes=10)
        power_nap = calculate_nap_recovery(minutes=20)
        long_nap = calculate_nap_recovery(minutes=45)
        assert short_nap < power_nap < long_nap

    def test_meal_recovery(self):
        """Test meal recovery calculation."""
        healthy = calculate_meal_recovery(is_healthy=True)
        unhealthy = calculate_meal_recovery(is_healthy=False)
        assert healthy > unhealthy


class TestCircadianFunctions:
    """Tests for circadian rhythm functions."""

    def test_get_circadian_modifier(self):
        """Test circadian modifier calculation."""
        morning = datetime(2024, 6, 15, 9, 0, 0)
        noon = datetime(2024, 6, 15, 12, 0, 0)
        evening = datetime(2024, 6, 15, 21, 0, 0)
        morning_mod = get_circadian_modifier(morning)
        noon_mod = get_circadian_modifier(noon)
        evening_mod = get_circadian_modifier(evening)
        assert -1 <= morning_mod <= 1
        assert -1 <= noon_mod <= 1
        assert -1 <= evening_mod <= 1

    def test_get_alertness_level(self):
        """Test alertness level calculation."""
        morning = datetime(2024, 6, 15, 9, 0, 0)
        alertness = get_alertness_level(morning, hours_awake=2)
        assert 0 <= alertness <= 1

    def test_alertness_decreases_with_time_awake(self):
        """Test that alertness decreases with hours awake."""
        morning = datetime(2024, 6, 15, 9, 0, 0)
        early = get_alertness_level(morning, hours_awake=2)
        late = get_alertness_level(morning, hours_awake=14)
        assert early > late

    def test_is_optimal_sleep_time(self):
        """Test optimal sleep time detection."""
        late_night = datetime(2024, 6, 15, 23, 0, 0)
        early_morning = datetime(2024, 6, 15, 4, 0, 0)
        midday = datetime(2024, 6, 15, 12, 0, 0)
        assert is_optimal_sleep_time(late_night) is True
        assert is_optimal_sleep_time(early_morning) is True
        assert is_optimal_sleep_time(midday) is False

    def test_get_recommended_wake_time(self):
        """Test recommended wake time calculation."""
        bedtime = datetime(2024, 6, 15, 22, 0, 0)
        wake_time = get_recommended_wake_time(bedtime, cycles=5)
        expected = bedtime + timedelta(minutes=15 + 90 * 5)
        assert wake_time == expected
