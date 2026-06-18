from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SessionListItem(BaseModel):
    session_id: str
    domain: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    total_fields: int
    resolved_local: int
    resolved_backend: int
    resolved_llm: int
    user_edited: int
    failed: int


class SessionListResponse(BaseModel):
    items: list[SessionListItem]
    next_cursor: str | None = None
