"""Tests for the Impact System API."""


from midori_ai_mood_engine import MealType
from midori_ai_mood_engine.impact import apply_stress
from midori_ai_mood_engine.impact import apply_relaxation
from midori_ai_mood_engine.impact import apply_exercise
from midori_ai_mood_engine.impact import apply_meal
from midori_ai_mood_engine.impact import apply_sleep_deprivation
from midori_ai_mood_engine.impact import apply_social_interaction
from midori_ai_mood_engine.impact import apply_rest


def test_apply_stress():
    """Test stress impact calculation."""
    impact = apply_stress(0.5)
    assert isinstance(impact, dict)
    assert "energy" in impact
    assert "irritability" in impact
    assert "anxiety" in impact
    assert impact["anxiety"] > 0
    assert impact["happiness"] < 0


def test_apply_stress_intensity_bounds():
    """Test that stress intensity is clamped."""
    low_impact = apply_stress(-0.5)
    _ = apply_stress(1.5)
    normal_impact = apply_stress(0.5)
    assert low_impact["anxiety"] < normal_impact["anxiety"]


def test_apply_relaxation():
    """Test relaxation impact calculation."""
    impact = apply_relaxation(0.7)
    assert isinstance(impact, dict)
    assert impact["happiness"] > 0
    assert impact["anxiety"] < 0
    assert impact["irritability"] < 0


def test_apply_exercise():
    """Test exercise impact calculation."""
    impact = apply_exercise(intensity=0.6, duration_minutes=30)
    assert isinstance(impact, dict)
    assert "happiness" in impact
    assert impact["happiness"] > 0
    assert impact["anxiety"] < 0


def test_apply_exercise_duration_effect():
    """Test that exercise duration affects impact."""
    short_impact = apply_exercise(0.5, 15)
    long_impact = apply_exercise(0.5, 60)
    assert abs(long_impact["happiness"]) > abs(short_impact["happiness"])


def test_apply_meal_types():
    """Test different meal type impacts."""
    breakfast = apply_meal(MealType.BREAKFAST)
    lunch = apply_meal(MealType.LUNCH)
    heavy = apply_meal(MealType.HEAVY)
    assert isinstance(breakfast, dict)
    assert isinstance(lunch, dict)
    assert isinstance(heavy, dict)
    assert breakfast.get("focus", 0) > 0


def test_apply_sleep_deprivation():
    """Test sleep deprivation impact calculation."""
    impact = apply_sleep_deprivation(hours=8)
    assert isinstance(impact, dict)
    assert impact["energy"] < 0
    assert impact["focus"] < 0
    assert impact["irritability"] > 0


def test_apply_sleep_deprivation_severity():
    """Test that more deprivation increases severity."""
    mild = apply_sleep_deprivation(4)
    severe = apply_sleep_deprivation(24)
    assert abs(severe["energy"]) > abs(mild["energy"])
    assert abs(severe["focus"]) > abs(mild["focus"])


def test_apply_social_interaction():
    """Test social interaction impact calculation."""
    impact = apply_social_interaction(quality=0.8, duration_minutes=30)
    assert isinstance(impact, dict)
    assert impact["happiness"] > 0
    assert impact["loneliness"] < 0
    assert impact["social_need"] < 0


def test_apply_social_interaction_quality_effect():
    """Test that interaction quality affects impact."""
    low_quality = apply_social_interaction(0.2, 30)
    high_quality = apply_social_interaction(0.9, 30)
    assert high_quality["happiness"] > low_quality["happiness"]


def test_apply_rest():
    """Test rest impact calculation."""
    impact = apply_rest(hours=8)
    assert isinstance(impact, dict)
    assert impact["energy"] > 0
    assert impact["anxiety"] < 0
    assert impact["focus"] > 0
