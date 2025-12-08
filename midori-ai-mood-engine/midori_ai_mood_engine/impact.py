"""Impact System API for external mood modifiers."""

from .enums import MealType


def apply_stress(intensity: float) -> dict[str, float]:
    """Apply stress impact. Raises cortisol and adrenaline effects."""
    intensity = max(0.0, min(1.0, intensity))
    return {"energy": -intensity * 0.2, "happiness": -intensity * 0.3, "irritability": intensity * 0.4, "anxiety": intensity * 0.5, "focus": -intensity * 0.3}


def apply_relaxation(intensity: float) -> dict[str, float]:
    """Apply relaxation impact. Raises oxytocin and serotonin effects."""
    intensity = max(0.0, min(1.0, intensity))
    return {"energy": intensity * 0.1, "happiness": intensity * 0.3, "irritability": -intensity * 0.3, "anxiety": -intensity * 0.4, "focus": intensity * 0.1}


def apply_exercise(intensity: float, duration_minutes: float) -> dict[str, float]:
    """Apply exercise impact. Raises endorphins, testosterone, depletes energy."""
    intensity = max(0.0, min(1.0, intensity))
    duration_factor = min(duration_minutes / 60.0, 2.0)
    energy_cost = intensity * duration_factor * 0.3
    endorphin_boost = intensity * duration_factor * 0.4
    return {"energy": -energy_cost + endorphin_boost * 0.2, "happiness": endorphin_boost, "irritability": -intensity * 0.2, "anxiety": -intensity * duration_factor * 0.3, "focus": intensity * 0.2, "libido": intensity * 0.1}


def apply_meal(meal_type: MealType) -> dict[str, float]:
    """Apply meal impact. Affects insulin, leptin, ghrelin."""
    meal_impacts = {MealType.BREAKFAST: {"energy": 0.2, "focus": 0.15, "irritability": -0.1}, MealType.LUNCH: {"energy": 0.15, "focus": -0.1, "happiness": 0.1}, MealType.DINNER: {"energy": 0.1, "happiness": 0.15, "anxiety": -0.1}, MealType.SNACK: {"energy": 0.05, "happiness": 0.05}, MealType.HEAVY: {"energy": -0.1, "focus": -0.2, "happiness": 0.2}, MealType.LIGHT: {"energy": 0.1, "focus": 0.1, "happiness": 0.05}}
    return meal_impacts.get(meal_type, {})


def apply_sleep_deprivation(hours: float) -> dict[str, float]:
    """Apply sleep deprivation impact. Affects melatonin, cortisol, energy."""
    hours = max(0.0, min(48.0, hours))
    severity = hours / 24.0
    return {"energy": -severity * 0.5, "happiness": -severity * 0.3, "irritability": severity * 0.4, "anxiety": severity * 0.3, "focus": -severity * 0.6, "mood_swings": severity * 0.3}


def apply_social_interaction(quality: float, duration_minutes: float) -> dict[str, float]:
    """Apply social interaction impact. Reduces loneliness, raises oxytocin."""
    quality = max(0.0, min(1.0, quality))
    duration_factor = min(duration_minutes / 60.0, 2.0)
    effect = quality * duration_factor
    return {"energy": effect * 0.1, "happiness": effect * 0.3, "irritability": -effect * 0.1, "anxiety": -effect * 0.2, "loneliness": -effect * 0.5, "social_need": -effect * 0.4}


def apply_rest(hours: float) -> dict[str, float]:
    """Apply rest impact. Restores energy, balances hormones."""
    hours = max(0.0, min(12.0, hours))
    recovery_factor = hours / 8.0
    return {"energy": recovery_factor * 0.6, "happiness": recovery_factor * 0.1, "irritability": -recovery_factor * 0.2, "anxiety": -recovery_factor * 0.2, "focus": recovery_factor * 0.3}
