"""Loneliness simulation subsystem."""

from .tracker import LonelinessTracker
from .tracker import InteractionRecord
from .social_need import SocialNeedModel
from .social_need import calculate_interaction_satisfaction
from .influence import calculate_loneliness_influence
from .influence import calculate_social_mood_boost


__all__ = ["LonelinessTracker", "InteractionRecord", "SocialNeedModel", "calculate_interaction_satisfaction", "calculate_loneliness_influence", "calculate_social_mood_boost"]
