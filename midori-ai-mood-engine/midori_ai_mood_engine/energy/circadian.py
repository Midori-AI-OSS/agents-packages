"""Circadian rhythm integration for energy modeling."""

import math

from datetime import datetime


def get_circadian_modifier(current_time: datetime) -> float:
    """Get circadian rhythm modifier based on time of day."""
    hour = current_time.hour + current_time.minute / 60.0
    phase = (hour - 6.0) / 24.0 * 2.0 * math.pi
    base_rhythm = math.sin(phase)
    afternoon_dip = -0.2 * math.exp(-((hour - 14.0) ** 2) / 4.0)
    return base_rhythm + afternoon_dip


def get_alertness_level(current_time: datetime, hours_awake: float) -> float:
    """Calculate alertness level based on time of day and hours awake."""
    circadian = get_circadian_modifier(current_time)
    circadian_normalized = (circadian + 1.0) / 2.0
    sleep_pressure = min(hours_awake / 16.0, 1.0)
    alertness = circadian_normalized * (1.0 - sleep_pressure * 0.5)
    return max(0.0, min(1.0, alertness))


def is_optimal_sleep_time(current_time: datetime) -> bool:
    """Check if current time is optimal for sleep."""
    hour = current_time.hour
    return hour >= 22 or hour < 6


def get_recommended_wake_time(bedtime: datetime, cycles: int = 5) -> datetime:
    """Calculate recommended wake time based on sleep cycles."""
    from datetime import timedelta

    cycle_duration = timedelta(minutes=90)
    sleep_onset = timedelta(minutes=15)
    total_sleep = sleep_onset + (cycle_duration * cycles)
    return bedtime + total_sleep
