"""Social need accumulation for loneliness simulation."""

from dataclasses import dataclass


@dataclass
class SocialNeedModel:
    """Model for social need accumulation over time."""
    base_need_rate: float = 0.1
    max_need: float = 1.0
    current_need: float = 0.0

    def accumulate(self, hours: float) -> float:
        """Accumulate social need over time."""
        increase = self.base_need_rate * hours
        self.current_need = min(self.max_need, self.current_need + increase)
        return self.current_need

    def satisfy(self, amount: float) -> float:
        """Satisfy social need by an amount."""
        self.current_need = max(0.0, self.current_need - amount)
        return self.current_need

    def get_urgency(self) -> float:
        """Get social need urgency (0-1 scale)."""
        return self.current_need / self.max_need

    def reset(self) -> None:
        """Reset social need to zero."""
        self.current_need = 0.0


def calculate_interaction_satisfaction(quality: float, duration_minutes: float) -> float:
    """Calculate how much an interaction satisfies social need."""
    base_satisfaction = min(duration_minutes / 60.0, 1.0)
    quality_multiplier = 0.5 + quality * 0.5
    return base_satisfaction * quality_multiplier
