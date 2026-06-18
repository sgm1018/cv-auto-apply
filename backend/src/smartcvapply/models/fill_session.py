"""FillSession audit document."""
from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field

from smartcvapply.utils.time import utcnow


class FillSession(Document):
    user_id: Annotated[PydanticObjectId, Indexed()]
    session_uuid: Annotated[UUID, Indexed(unique=True)] = Field(default_factory=uuid4)
    domain: str
    url_hash: str
    started_at: datetime = Field(default_factory=utcnow)
    ended_at: datetime | None = None
    total_fields: int = 0
    resolved_local: int = 0
    resolved_backend: int = 0
    resolved_llm: int = 0
    user_edited: int = 0
    failed: int = 0
    submitted: bool = False

    class Settings:
        name = "fill_sessions"
        use_state_management = True
        indexes = [[("user_id", 1), ("started_at", -1)]]
