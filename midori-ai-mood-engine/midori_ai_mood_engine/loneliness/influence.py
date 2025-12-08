"""Loneliness-to-mood influence calculations."""


def calculate_loneliness_influence(hours_since_interaction: float, social_need: float, interaction_quality: float) -> dict[str, float]:
    """Calculate mood influences from loneliness state."""
    time_factor = min(hours_since_interaction / 48.0, 1.0)
    need_factor = social_need
    quality_deficit = 1.0 - interaction_quality

    loneliness_score = (time_factor * 0.4 + need_factor * 0.4 + quality_deficit * 0.2)

    return {"loneliness": loneliness_score, "happiness_modifier": -loneliness_score * 0.3, "anxiety_modifier": loneliness_score * 0.2, "energy_modifier": -loneliness_score * 0.15, "irritability_modifier": loneliness_score * 0.1}


def calculate_social_mood_boost(quality: float, duration_minutes: float) -> dict[str, float]:
    """Calculate positive mood effects from a social interaction."""
    duration_factor = min(duration_minutes / 60.0, 1.0)
    effect_strength = quality * duration_factor

    return {"happiness_boost": effect_strength * 0.3, "anxiety_reduction": effect_strength * 0.2, "energy_boost": effect_strength * 0.1, "loneliness_reduction": effect_strength * 0.5}
