"""LearnedMapping document."""
from datetime import datetime
from typing import Annotated, Literal

from beanie import Document, Indexed
from pydantic import Field

from cvapplier.utils.time import utcnow


class LearnedMapping(Document):
    field_signature: Annotated[str, Indexed()]
    language: Annotated[Literal["en", "es"], Indexed()]
    target_path: str
    transform: str | None = None
    confidence: float = 0.85
    usage_count: int = 0
    user_count: int = 0
    source: Literal["user_confirmed", "user_edited", "llm_verified"] = "user_confirmed"
    last_used_at: datetime = Field(default_factory=utcnow)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "learned_mappings"
        use_state_management = True
        indexes = [
            [("field_signature", 1), ("language", 1)],
            [("usage_count", -1)],
        ]
