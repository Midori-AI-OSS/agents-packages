"""Tests for the loneliness simulation subsystem."""

import pytest

from datetime import datetime
from datetime import timedelta

from midori_ai_mood_engine.loneliness import LonelinessTracker
from midori_ai_mood_engine.loneliness import SocialNeedModel
from midori_ai_mood_engine.loneliness import calculate_interaction_satisfaction
from midori_ai_mood_engine.loneliness import calculate_loneliness_influence
from midori_ai_mood_engine.loneliness import calculate_social_mood_boost


@pytest.fixture
def tracker():
    """Create a test loneliness tracker."""
    return LonelinessTracker()


@pytest.fixture
def social_need():
    """Create a test social need model."""
    return SocialNeedModel()


class TestLonelinessTracker:
    """Tests for LonelinessTracker."""

    def test_initialization(self, tracker):
        """Test tracker initialization."""
        assert tracker.last_interaction is None
        assert len(tracker.interaction_history) == 0

    def test_record_interaction(self, tracker):
        """Test recording an interaction."""
        tracker.record_interaction(quality=0.8, duration_minutes=30)
        assert tracker.last_interaction is not None
        assert len(tracker.interaction_history) == 1

    def test_get_hours_since_interaction_no_history(self, tracker):
        """Test hours since interaction with no history."""
        hours = tracker.get_hours_since_interaction()
        assert hours == 48.0

    def test_get_hours_since_interaction(self, tracker):
        """Test hours since interaction with history."""
        now = datetime.now()
        past = now - timedelta(hours=5)
        tracker.record_interaction(quality=0.8, duration_minutes=30, timestamp=past)
        hours = tracker.get_hours_since_interaction(now)
        assert 4.9 < hours < 5.1

    def test_get_recent_interaction_quality(self, tracker):
        """Test getting recent interaction quality."""
        now = datetime.now()
        tracker.record_interaction(0.9, 30, now - timedelta(hours=1))
        tracker.record_interaction(0.5, 60, now - timedelta(hours=2))
        quality = tracker.get_recent_interaction_quality(hours=24, current_time=now)
        assert 0 < quality < 1

    def test_get_interaction_frequency(self, tracker):
        """Test getting interaction frequency."""
        now = datetime.now()
        for i in range(7):
            tracker.record_interaction(0.7, 30, now - timedelta(days=i))
        frequency = tracker.get_interaction_frequency(hours=168, current_time=now)
        assert frequency == 1.0

    def test_max_history_size(self, tracker):
        """Test that history is limited to max size."""
        tracker.max_history_size = 5
        for i in range(10):
            tracker.record_interaction(0.5, 30)
        assert len(tracker.interaction_history) == 5


class TestSocialNeedModel:
    """Tests for SocialNeedModel."""

    def test_initialization(self, social_need):
        """Test social need initialization."""
        assert social_need.current_need == 0.0

    def test_accumulate(self, social_need):
        """Test need accumulation."""
        social_need.accumulate(hours=10)
        assert social_need.current_need == 1.0

    def test_accumulate_capped(self, social_need):
        """Test that need is capped at max."""
        social_need.accumulate(hours=100)
        assert social_need.current_need == social_need.max_need

    def test_satisfy(self, social_need):
        """Test satisfying need."""
        social_need.current_need = 0.8
        social_need.satisfy(0.3)
        assert social_need.current_need == 0.5

    def test_satisfy_floor(self, social_need):
        """Test that need doesn't go below zero."""
        social_need.current_need = 0.2
        social_need.satisfy(0.5)
        assert social_need.current_need == 0.0

    def test_get_urgency(self, social_need):
        """Test getting urgency."""
        social_need.current_need = 0.5
        assert social_need.get_urgency() == 0.5

    def test_reset(self, social_need):
        """Test resetting need."""
        social_need.current_need = 0.8
        social_need.reset()
        assert social_need.current_need == 0.0


class TestInfluenceFunctions:
    """Tests for influence calculation functions."""

    def test_calculate_interaction_satisfaction(self):
        """Test interaction satisfaction calculation."""
        satisfaction = calculate_interaction_satisfaction(quality=1.0, duration_minutes=60)
        assert 0 < satisfaction <= 1

    def test_calculate_loneliness_influence(self):
        """Test loneliness influence calculation."""
        influence = calculate_loneliness_influence(hours_since_interaction=24, social_need=0.5, interaction_quality=0.3)
        assert isinstance(influence, dict)
        assert "loneliness" in influence
        assert "happiness_modifier" in influence
        assert influence["happiness_modifier"] < 0

    def test_calculate_social_mood_boost(self):
        """Test social mood boost calculation."""
        boost = calculate_social_mood_boost(quality=0.8, duration_minutes=30)
        assert isinstance(boost, dict)
        assert "happiness_boost" in boost
        assert boost["happiness_boost"] > 0
        assert "loneliness_reduction" in boost
        assert boost["loneliness_reduction"] > 0
