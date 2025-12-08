"""Enumerations for the mood engine package."""

from enum import Enum


class StepType(str, Enum):
    """Resolution type for hormone cycle simulation."""
    DAY = "day"
    PULSE = "pulse"
    FULL = "full"


class Gender(str, Enum):
    """Gender configuration for mood profile."""
    FEMALE = "female"
    MALE = "male"
    CUSTOM = "custom"


class MealType(str, Enum):
    """Types of meals for impact system."""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
    HEAVY = "heavy"
    LIGHT = "light"


class InteractionQuality(str, Enum):
    """Quality levels for social interactions."""
    POOR = "poor"
    AVERAGE = "average"
    GOOD = "good"
    EXCELLENT = "excellent"


class HormoneCategory(str, Enum):
    """Categories for hormone classification."""
    REPRODUCTIVE = "reproductive"
    STRESS = "stress"
    MOOD = "mood"
    METABOLISM = "metabolism"
