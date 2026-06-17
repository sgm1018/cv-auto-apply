"""FeedbackEvent document."""
from datetime import datetime
from typing import Annotated, Literal

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field

from cvapplier.utils.time import utcnow


class FeedbackEvent(Document):
    session_id: Annotated[PydanticObjectId, Indexed()]
    user_id: Annotated[PydanticObjectId, Indexed()]
    field_signature: str
    language: Literal["en", "es"]
    source: Literal["local", "learned", "llm"]
    action: Literal["confirmed", "edited", "rejected"]
    suggested_hash: str
    actual_hash: str | None = None
    timestamp: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "feedback_events"
        use_state_management = True
        indexes = [
            [("session_id", 1), ("timestamp", 1)],
            [("field_signature", 1), ("action", 1)],
        ]
