"""Parsing probability decay calculations for media lifecycle."""

import random

from datetime import datetime
from datetime import timezone


class DecayConfig:
    """Configuration for decay timeline.

    Attributes:
        full_probability_minutes: Minutes during which parsing probability is 100%
        zero_probability_minutes: Minutes at which parsing probability reaches 0%
    """

    def __init__(self, full_probability_minutes: float = 35.0, zero_probability_minutes: float = 90.0) -> None:
        """Initialize decay configuration.

        Args:
            full_probability_minutes: Minutes with 100% probability (default 35)
            zero_probability_minutes: Minutes with 0% probability (default 90)
        """
        if full_probability_minutes < 0:
            raise ValueError("full_probability_minutes must be non-negative")
        if zero_probability_minutes <= full_probability_minutes:
            raise ValueError("zero_probability_minutes must be greater than full_probability_minutes")
        self.full_probability_minutes = full_probability_minutes
        self.zero_probability_minutes = zero_probability_minutes

    @property
    def decay_window_minutes(self) -> float:
        """Duration of the decay window in minutes."""
        return self.zero_probability_minutes - self.full_probability_minutes


def get_age_minutes(time_saved: datetime) -> float:
    """Calculate age of media in minutes from time_saved to now.

    Args:
        time_saved: When the media was saved (must be timezone-aware)

    Returns:
        Age in minutes as a float
    """
    now = datetime.now(timezone.utc)
    if time_saved.tzinfo is None:
        time_saved = time_saved.replace(tzinfo=timezone.utc)
    delta = now - time_saved
    return delta.total_seconds() / 60.0


def get_parsing_probability(time_saved: datetime, config: DecayConfig | None = None) -> float:
    """Calculate parsing probability based on media age.

    Timeline:
    - 0 to full_probability_minutes: 100% probability
    - full_probability_minutes to zero_probability_minutes: Linear decay
    - After zero_probability_minutes: 0% probability

    Args:
        time_saved: When the media was saved
        config: Decay configuration (uses defaults if None)

    Returns:
        Probability as float from 0.0 to 1.0
    """
    if config is None:
        config = DecayConfig()
    age_minutes = get_age_minutes(time_saved)
    if age_minutes <= config.full_probability_minutes:
        return 1.0
    if age_minutes >= config.zero_probability_minutes:
        return 0.0
    elapsed_in_window = age_minutes - config.full_probability_minutes
    decay_fraction = elapsed_in_window / config.decay_window_minutes
    return 1.0 - decay_fraction


def should_parse(time_saved: datetime, config: DecayConfig | None = None) -> bool:
    """Determine probabilistically whether to parse based on age.

    Uses the parsing probability to make a random decision.

    Args:
        time_saved: When the media was saved
        config: Decay configuration (uses defaults if None)

    Returns:
        True if should parse, False otherwise
    """
    probability = get_parsing_probability(time_saved, config)
    return random.random() < probability


def is_aged_out(time_saved: datetime, config: DecayConfig | None = None) -> bool:
    """Check if media has aged out and should be cleaned up.

    Media is aged out when it passes the zero_probability_minutes threshold.

    Args:
        time_saved: When the media was saved
        config: Decay configuration (uses defaults if None)

    Returns:
        True if aged out, False otherwise
    """
    if config is None:
        config = DecayConfig()
    age_minutes = get_age_minutes(time_saved)
    return age_minutes >= config.zero_probability_minutes
