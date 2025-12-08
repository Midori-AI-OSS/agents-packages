"""Time-since-interaction tracking for loneliness simulation."""

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timedelta


DEFAULT_HOURS_SINCE_INTERACTION = 48.0


@dataclass
class InteractionRecord:
    """Record of a social interaction."""
    timestamp: datetime
    quality: float
    duration_minutes: float


@dataclass
class LonelinessTracker:
    """Tracks time since last meaningful interaction."""
    last_interaction: datetime | None = None
    interaction_history: list[InteractionRecord] = field(default_factory=list)
    max_history_size: int = 100

    def record_interaction(self, quality: float, duration_minutes: float, timestamp: datetime | None = None) -> None:
        """Record a social interaction."""
        if timestamp is None:
            timestamp = datetime.now()

        self.last_interaction = timestamp
        record = InteractionRecord(timestamp=timestamp, quality=quality, duration_minutes=duration_minutes)
        self.interaction_history.append(record)

        if len(self.interaction_history) > self.max_history_size:
            self.interaction_history = self.interaction_history[-self.max_history_size:]

    def get_hours_since_interaction(self, current_time: datetime | None = None) -> float:
        """Get hours since last meaningful interaction."""
        if self.last_interaction is None:
            return DEFAULT_HOURS_SINCE_INTERACTION

        if current_time is None:
            current_time = datetime.now()

        delta = current_time - self.last_interaction
        return delta.total_seconds() / 3600.0

    def get_recent_interaction_quality(self, hours: float = 24.0, current_time: datetime | None = None) -> float:
        """Get average quality of recent interactions."""
        if current_time is None:
            current_time = datetime.now()

        cutoff = current_time - timedelta(hours=hours)
        recent = [r for r in self.interaction_history if r.timestamp > cutoff]

        if not recent:
            return 0.0

        total_quality = sum(r.quality * r.duration_minutes for r in recent)
        total_duration = sum(r.duration_minutes for r in recent)

        if total_duration == 0:
            return 0.0

        return total_quality / total_duration

    def get_interaction_frequency(self, hours: float = 168.0, current_time: datetime | None = None) -> float:
        """Get interaction frequency (interactions per day) over the specified period."""
        if current_time is None:
            current_time = datetime.now()

        cutoff = current_time - timedelta(hours=hours)
        recent = [r for r in self.interaction_history if r.timestamp > cutoff]

        days = hours / 24.0
        return len(recent) / days if days > 0 else 0.0
