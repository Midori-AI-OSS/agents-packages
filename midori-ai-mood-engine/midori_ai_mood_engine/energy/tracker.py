"""Base energy level tracking."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class EnergyTracker:
    """Tracks base energy levels over time."""
    current_energy: float = 100.0
    max_energy: float = 100.0
    min_energy: float = 0.0
    last_update: datetime | None = None
    passive_drain_rate: float = 2.0

    def update(self, current_time: datetime | None = None) -> float:
        """Update energy with passive drain."""
        if current_time is None:
            current_time = datetime.now()

        if self.last_update is not None:
            hours_elapsed = (current_time - self.last_update).total_seconds() / 3600.0
            drain = self.passive_drain_rate * hours_elapsed
            self.current_energy = max(self.min_energy, self.current_energy - drain)

        self.last_update = current_time
        return self.current_energy

    def expend(self, amount: float) -> float:
        """Expend energy by an amount."""
        self.current_energy = max(self.min_energy, self.current_energy - amount)
        return self.current_energy

    def recover(self, amount: float) -> float:
        """Recover energy by an amount."""
        self.current_energy = min(self.max_energy, self.current_energy + amount)
        return self.current_energy

    def get_level(self) -> float:
        """Get current energy level as a percentage."""
        return self.current_energy / self.max_energy

    def get_fatigue_level(self) -> float:
        """Get fatigue level (inverse of energy)."""
        return 1.0 - self.get_level()

    def reset(self) -> None:
        """Reset energy to maximum."""
        self.current_energy = self.max_energy
