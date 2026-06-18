"""Beanie Documents for MongoDB persistence."""
from smartcvapply.models.cv import CV
from smartcvapply.models.feedback_event import FeedbackEvent
from smartcvapply.models.fill_session import FillSession
from smartcvapply.models.learned_mapping import LearnedMapping
from smartcvapply.models.profile import Profile
from smartcvapply.models.user import User

__all__ = [
    "User",
    "Profile",
    "CV",
    "LearnedMapping",
    "FillSession",
    "FeedbackEvent",
]
