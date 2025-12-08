"""Activity-based energy expenditure."""


def calculate_exercise_expenditure(intensity: float, duration_minutes: float) -> float:
    """Calculate energy expenditure from exercise."""
    base_expenditure = duration_minutes * 0.5
    intensity_multiplier = 1.0 + intensity * 2.0
    return base_expenditure * intensity_multiplier


def calculate_mental_work_expenditure(intensity: float, duration_minutes: float) -> float:
    """Calculate energy expenditure from mental work."""
    base_expenditure = duration_minutes * 0.2
    intensity_multiplier = 1.0 + intensity * 1.0
    return base_expenditure * intensity_multiplier


def calculate_stress_expenditure(intensity: float, duration_minutes: float) -> float:
    """Calculate energy expenditure from stress."""
    base_expenditure = duration_minutes * 0.3
    intensity_multiplier = 1.0 + intensity * 1.5
    return base_expenditure * intensity_multiplier


def calculate_social_expenditure(intensity: float, duration_minutes: float) -> float:
    """Calculate energy expenditure from social interaction."""
    base_expenditure = duration_minutes * 0.1
    intensity_multiplier = 1.0 + intensity * 0.5
    return base_expenditure * intensity_multiplier
