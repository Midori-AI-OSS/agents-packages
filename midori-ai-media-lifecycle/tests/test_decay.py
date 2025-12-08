"""Tests for decay calculations."""

import pytest

from datetime import datetime
from datetime import timedelta
from datetime import timezone

from midori_ai_media_lifecycle import DecayConfig
from midori_ai_media_lifecycle import get_age_minutes
from midori_ai_media_lifecycle import get_parsing_probability
from midori_ai_media_lifecycle import is_aged_out
from midori_ai_media_lifecycle import should_parse


class TestDecayConfig:
    """Tests for DecayConfig class."""

    def test_default_values(self) -> None:
        config = DecayConfig()
        assert config.full_probability_minutes == 35.0
        assert config.zero_probability_minutes == 90.0

    def test_custom_values(self) -> None:
        config = DecayConfig(full_probability_minutes=10.0, zero_probability_minutes=60.0)
        assert config.full_probability_minutes == 10.0
        assert config.zero_probability_minutes == 60.0

    def test_decay_window_minutes(self) -> None:
        config = DecayConfig(full_probability_minutes=10.0, zero_probability_minutes=60.0)
        assert config.decay_window_minutes == 50.0

    def test_default_decay_window(self) -> None:
        config = DecayConfig()
        assert config.decay_window_minutes == 55.0

    def test_negative_full_probability_raises(self) -> None:
        with pytest.raises(ValueError, match="must be non-negative"):
            DecayConfig(full_probability_minutes=-1.0)

    def test_zero_less_than_full_raises(self) -> None:
        with pytest.raises(ValueError, match="must be greater than"):
            DecayConfig(full_probability_minutes=90.0, zero_probability_minutes=35.0)

    def test_equal_values_raises(self) -> None:
        with pytest.raises(ValueError, match="must be greater than"):
            DecayConfig(full_probability_minutes=50.0, zero_probability_minutes=50.0)


class TestGetAgeMinutes:
    """Tests for get_age_minutes function."""

    def test_fresh_media(self) -> None:
        now = datetime.now(timezone.utc)
        age = get_age_minutes(now)
        assert age >= 0.0
        assert age < 0.1

    def test_one_hour_old(self) -> None:
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        age = get_age_minutes(one_hour_ago)
        assert 59.9 < age < 60.1

    def test_thirty_minutes_old(self) -> None:
        thirty_min_ago = datetime.now(timezone.utc) - timedelta(minutes=30)
        age = get_age_minutes(thirty_min_ago)
        assert 29.9 < age < 30.1

    def test_naive_datetime_treated_as_utc(self) -> None:
        now = datetime.now(timezone.utc)
        naive_now = now.replace(tzinfo=None)
        age = get_age_minutes(naive_now)
        assert age >= 0.0
        assert age < 0.1


class TestGetParsingProbability:
    """Tests for get_parsing_probability function."""

    def test_fresh_media_full_probability(self) -> None:
        now = datetime.now(timezone.utc)
        probability = get_parsing_probability(now)
        assert probability == 1.0

    def test_at_full_threshold_still_full(self) -> None:
        config = DecayConfig()
        time_saved = datetime.now(timezone.utc) - timedelta(minutes=35)
        probability = get_parsing_probability(time_saved, config)
        assert probability >= 0.99

    def test_at_zero_threshold_zero(self) -> None:
        config = DecayConfig()
        time_saved = datetime.now(timezone.utc) - timedelta(minutes=90)
        probability = get_parsing_probability(time_saved, config)
        assert probability == 0.0

    def test_past_zero_threshold_zero(self) -> None:
        config = DecayConfig()
        time_saved = datetime.now(timezone.utc) - timedelta(minutes=120)
        probability = get_parsing_probability(time_saved, config)
        assert probability == 0.0

    def test_midpoint_approximately_half(self) -> None:
        config = DecayConfig(full_probability_minutes=0.0, zero_probability_minutes=100.0)
        time_saved = datetime.now(timezone.utc) - timedelta(minutes=50)
        probability = get_parsing_probability(time_saved, config)
        assert 0.45 < probability < 0.55

    def test_linear_decay(self) -> None:
        config = DecayConfig(full_probability_minutes=0.0, zero_probability_minutes=100.0)
        p25 = get_parsing_probability(datetime.now(timezone.utc) - timedelta(minutes=25), config)
        p50 = get_parsing_probability(datetime.now(timezone.utc) - timedelta(minutes=50), config)
        p75 = get_parsing_probability(datetime.now(timezone.utc) - timedelta(minutes=75), config)
        assert 0.70 < p25 < 0.80
        assert 0.45 < p50 < 0.55
        assert 0.20 < p75 < 0.30

    def test_uses_default_config(self) -> None:
        now = datetime.now(timezone.utc)
        probability = get_parsing_probability(now)
        assert probability == 1.0

    def test_custom_config_respected(self) -> None:
        config = DecayConfig(full_probability_minutes=0.0, zero_probability_minutes=10.0)
        time_saved = datetime.now(timezone.utc) - timedelta(minutes=5)
        probability = get_parsing_probability(time_saved, config)
        assert 0.45 < probability < 0.55


class TestShouldParse:
    """Tests for should_parse function."""

    def test_fresh_media_always_true(self) -> None:
        now = datetime.now(timezone.utc)
        results = [should_parse(now) for _ in range(100)]
        assert all(results)

    def test_aged_out_media_always_false(self) -> None:
        config = DecayConfig()
        time_saved = datetime.now(timezone.utc) - timedelta(minutes=120)
        results = [should_parse(time_saved, config) for _ in range(100)]
        assert not any(results)

    def test_probabilistic_in_decay_window(self) -> None:
        config = DecayConfig(full_probability_minutes=0.0, zero_probability_minutes=100.0)
        time_saved = datetime.now(timezone.utc) - timedelta(minutes=50)
        results = [should_parse(time_saved, config) for _ in range(1000)]
        true_count = sum(results)
        assert 350 < true_count < 650


class TestIsAgedOut:
    """Tests for is_aged_out function."""

    def test_fresh_media_not_aged_out(self) -> None:
        now = datetime.now(timezone.utc)
        assert is_aged_out(now) is False

    def test_at_threshold_aged_out(self) -> None:
        config = DecayConfig()
        time_saved = datetime.now(timezone.utc) - timedelta(minutes=90)
        assert is_aged_out(time_saved, config) is True

    def test_past_threshold_aged_out(self) -> None:
        config = DecayConfig()
        time_saved = datetime.now(timezone.utc) - timedelta(minutes=120)
        assert is_aged_out(time_saved, config) is True

    def test_just_before_threshold_not_aged_out(self) -> None:
        config = DecayConfig()
        time_saved = datetime.now(timezone.utc) - timedelta(minutes=89)
        assert is_aged_out(time_saved, config) is False

    def test_uses_default_config(self) -> None:
        now = datetime.now(timezone.utc)
        assert is_aged_out(now) is False

    def test_custom_config_respected(self) -> None:
        config = DecayConfig(full_probability_minutes=0.0, zero_probability_minutes=10.0)
        time_saved = datetime.now(timezone.utc) - timedelta(minutes=15)
        assert is_aged_out(time_saved, config) is True
