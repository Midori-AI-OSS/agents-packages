"""Profile configuration for the mood engine."""

from dataclasses import dataclass

from .enums import Gender


@dataclass
class MoodProfile:
    """User profile configuration affecting mood calculations."""
    gender: Gender = Gender.FEMALE
    age: int = 25
    modifier: float = 1.0
    cycle_enabled: bool = True
    loneliness_enabled: bool = True
    energy_enabled: bool = True

    def get_age_modifier(self) -> float:
        """Calculate age-based baseline modifier."""
        if self.age < 18:
            return 1.2
        elif self.age < 25:
            return 1.1
        elif self.age < 35:
            return 1.0
        elif self.age < 45:
            return 0.95
        elif self.age < 55:
            return 0.85
        else:
            return 0.75

    def get_gender_hormone_multipliers(self) -> dict[str, float]:
        """Get hormone multipliers based on gender."""
        if self.gender == Gender.FEMALE:
            return {"estradiol": 1.0, "progesterone": 1.0, "testosterone": 0.3, "fsh": 1.0, "lh": 1.0}
        elif self.gender == Gender.MALE:
            return {"estradiol": 0.1, "progesterone": 0.1, "testosterone": 1.0, "fsh": 0.5, "lh": 0.5}
        else:
            return {"estradiol": 0.5, "progesterone": 0.5, "testosterone": 0.5, "fsh": 0.75, "lh": 0.75}

    def apply_modifier(self, value: float) -> float:
        """Apply the global modifier to a value."""
        return value * self.modifier * self.get_age_modifier()


@dataclass
class MoodState:
    """Current mood state snapshot."""
    energy: float = 0.0
    happiness: float = 0.0
    irritability: float = 0.0
    anxiety: float = 0.0
    focus: float = 0.0
    loneliness: float = 0.0
    mood_swings: float = 0.0
    libido: float = 0.0
    sleep_quality: float = 0.0
    social_need: float = 0.0

    def to_dict(self) -> dict[str, float]:
        """Convert mood state to dictionary."""
        return {"energy": self.energy, "happiness": self.happiness, "irritability": self.irritability, "anxiety": self.anxiety, "focus": self.focus, "loneliness": self.loneliness, "mood_swings": self.mood_swings, "libido": self.libido, "sleep_quality": self.sleep_quality, "social_need": self.social_need}

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> "MoodState":
        """Create mood state from dictionary."""
        return cls(energy=data.get("energy", 0.0), happiness=data.get("happiness", 0.0), irritability=data.get("irritability", 0.0), anxiety=data.get("anxiety", 0.0), focus=data.get("focus", 0.0), loneliness=data.get("loneliness", 0.0), mood_swings=data.get("mood_swings", 0.0), libido=data.get("libido", 0.0), sleep_quality=data.get("sleep_quality", 0.0), social_need=data.get("social_need", 0.0))
