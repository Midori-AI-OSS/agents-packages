"""Rest and sleep energy recovery."""


def calculate_sleep_recovery(hours: float, quality: float = 1.0) -> float:
    """Calculate energy recovery from sleep."""
    base_recovery = hours * 12.5
    quality_multiplier = 0.5 + quality * 0.5
    return base_recovery * quality_multiplier


def calculate_rest_recovery(hours: float) -> float:
    """Calculate energy recovery from rest (not sleep)."""
    return hours * 5.0


def calculate_nap_recovery(minutes: float) -> float:
    """Calculate energy recovery from a nap."""
    if minutes < 10:
        return minutes * 0.5
    elif minutes <= 30:
        return 5.0 + (minutes - 10) * 0.8
    else:
        return 21.0 + (minutes - 30) * 0.3


def calculate_meal_recovery(is_healthy: bool = True) -> float:
    """Calculate energy recovery from a meal."""
    base_recovery = 5.0
    if is_healthy:
        return base_recovery * 1.2
    else:
        return base_recovery * 0.8
