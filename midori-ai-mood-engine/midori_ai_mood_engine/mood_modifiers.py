"""Unified mood calculation combining all subsystems."""

from .profile import MoodState


def calculate_unified_mood(hormone_mods: dict[str, float], loneliness_influence: dict[str, float], energy_level: float, circadian_modifier: float, profile_modifier: float = 1.0) -> MoodState:
    """Calculate unified mood state from all subsystems."""
    base_energy = hormone_mods.get("energy", 0.0)
    energy_from_tracker = (energy_level - 0.5) * 2.0
    circadian_energy = circadian_modifier * 0.3
    loneliness_energy_mod = loneliness_influence.get("energy_modifier", 0.0)
    final_energy = (base_energy + energy_from_tracker + circadian_energy + loneliness_energy_mod) * profile_modifier

    base_happiness = hormone_mods.get("happiness", 0.0)
    loneliness_happiness_mod = loneliness_influence.get("happiness_modifier", 0.0)
    final_happiness = (base_happiness + loneliness_happiness_mod) * profile_modifier

    base_irritability = hormone_mods.get("irritability", 0.0)
    loneliness_irritability_mod = loneliness_influence.get("irritability_modifier", 0.0)
    fatigue_irritability = max(0, (0.5 - energy_level) * 0.5)
    final_irritability = (base_irritability + loneliness_irritability_mod + fatigue_irritability) * profile_modifier

    base_anxiety = hormone_mods.get("anxiety", 0.0)
    loneliness_anxiety_mod = loneliness_influence.get("anxiety_modifier", 0.0)
    final_anxiety = (base_anxiety + loneliness_anxiety_mod) * profile_modifier

    base_focus = hormone_mods.get("focus", 0.0)
    energy_focus = (energy_level - 0.3) * 0.5
    circadian_focus = circadian_modifier * 0.2
    final_focus = (base_focus + energy_focus + circadian_focus) * profile_modifier

    loneliness_score = loneliness_influence.get("loneliness", 0.0)

    mood_swings = hormone_mods.get("mood_swings", 0.0) * profile_modifier
    libido = hormone_mods.get("libido", 0.0) * profile_modifier
    sleep_quality = hormone_mods.get("sleep_quality", 0.0) * profile_modifier
    social_need = loneliness_score * 0.8

    return MoodState(energy=final_energy, happiness=final_happiness, irritability=final_irritability, anxiety=final_anxiety, focus=final_focus, loneliness=loneliness_score, mood_swings=mood_swings, libido=libido, sleep_quality=sleep_quality, social_need=social_need)


def apply_impact_to_mood(current_mood: MoodState, impact: dict[str, float]) -> MoodState:
    """Apply an impact event to the current mood state."""
    return MoodState(energy=current_mood.energy + impact.get("energy", 0.0), happiness=current_mood.happiness + impact.get("happiness", 0.0), irritability=current_mood.irritability + impact.get("irritability", 0.0), anxiety=current_mood.anxiety + impact.get("anxiety", 0.0), focus=current_mood.focus + impact.get("focus", 0.0), loneliness=current_mood.loneliness + impact.get("loneliness", 0.0), mood_swings=current_mood.mood_swings + impact.get("mood_swings", 0.0), libido=current_mood.libido + impact.get("libido", 0.0), sleep_quality=current_mood.sleep_quality + impact.get("sleep_quality", 0.0), social_need=current_mood.social_need + impact.get("social_need", 0.0))
