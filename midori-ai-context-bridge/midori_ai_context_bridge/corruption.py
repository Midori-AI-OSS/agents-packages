"""Time-based memory corruption logic.

This module implements gradual memory degradation based on age.
Older data gets increasingly corrupted before eventual removal.
"""

import random

from typing import Optional
from typing import Tuple

from .config import DecayConfig


class MemoryCorruptor:
    """Applies time-based corruption to stored reasoning text.

    Corruption simulates natural memory degradation:
    - Fresh data (age < decay_minutes): No corruption
    - Aging data (decay_minutes <= age < removal_minutes): Progressive corruption
    - Old data (age >= removal_minutes): Marked for removal
    """

    def __init__(self, decay_config: DecayConfig, seed: Optional[int] = None) -> None:
        """Initialize the corruptor with decay configuration.

        Args:
            decay_config: Configuration for decay timing and intensity
            seed: Optional random seed for reproducible corruption
        """
        self._config = decay_config
        self._rng = random.Random(seed)

    @property
    def decay_minutes(self) -> int:
        """Return decay threshold in minutes."""
        return self._config.decay_minutes

    @property
    def removal_minutes(self) -> float:
        """Return removal threshold in minutes."""
        return self._config.removal_minutes

    def calculate_severity(self, age_minutes: float) -> float:
        """Calculate corruption severity based on age.

        Args:
            age_minutes: Age of the data in minutes

        Returns:
            Severity value between 0.0 (no corruption) and 1.0 (max corruption)
        """
        if age_minutes < self._config.decay_minutes:
            return 0.0
        time_range = self._config.removal_minutes - self._config.decay_minutes
        if time_range <= 0:
            return 1.0
        severity = (age_minutes - self._config.decay_minutes) / time_range
        return min(1.0, max(0.0, severity))

    def corrupt_text(self, text: str, age_minutes: float) -> str:
        """Apply corruption based on age.

        Args:
            text: Original text to potentially corrupt
            age_minutes: Age of the data in minutes

        Returns:
            Corrupted text with random character modifications/removals
        """
        severity = self.calculate_severity(age_minutes)
        if severity <= 0.0:
            return text
        corruption_rate = severity * self._config.corruption_intensity
        corrupted_chars = []
        for char in text:
            if self._rng.random() < corruption_rate:
                if self._rng.random() < 0.5:
                    continue
                else:
                    corrupted_chars.append(self._rng.choice("abcdefghijklmnopqrstuvwxyz "))
            else:
                corrupted_chars.append(char)
        return "".join(corrupted_chars)

    def should_remove(self, age_minutes: float) -> bool:
        """Check if data should be permanently removed.

        Args:
            age_minutes: Age of the data in minutes

        Returns:
            True if data is old enough to remove
        """
        return age_minutes >= self._config.removal_minutes

    def process_text(self, text: str, age_minutes: float) -> Tuple[str | None, bool]:
        """Process text with corruption and removal logic.

        Args:
            text: Original text
            age_minutes: Age of the data in minutes

        Returns:
            Tuple of (corrupted_text_or_none, should_remove)
            Returns (None, True) if data should be removed
        """
        if self.should_remove(age_minutes):
            return None, True
        corrupted = self.corrupt_text(text, age_minutes)
        return corrupted, False
