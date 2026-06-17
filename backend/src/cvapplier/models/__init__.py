"""Beanie Documents for MongoDB persistence."""
from cvapplier.models.cv import CV
from cvapplier.models.feedback_event import FeedbackEvent
from cvapplier.models.fill_session import FillSession
from cvapplier.models.learned_mapping import LearnedMapping
from cvapplier.models.profile import Profile
from cvapplier.models.user import User

__all__ = [
    "User",
    "Profile",
    "CV",
    "LearnedMapping",
    "FillSession",
    "FeedbackEvent",
]
