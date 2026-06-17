"""WebSocket message types shared between extension and backend."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ExtractedFieldWS(BaseModel):
    field_id: str
    label: Optional[str] = None
    type: Optional[str] = None
    name: Optional[str] = None
    placeholder: Optional[str] = None
    required: bool = False
    options: Optional[list[dict[str, str]]] = None
    current_value: Optional[str] = None
    context: Optional[str] = None


class FillRequest(BaseModel):
    type: Literal["FILL_REQUEST"] = "FILL_REQUEST"
    url_hash: str
    domain: str
    fields: list[ExtractedFieldWS] = Field(default_factory=list)


class ProgressMsg(BaseModel):
    type: Literal["FILL_PROGRESS"] = "FILL_PROGRESS"
    field_id: str
    status: Literal["local", "learned", "llm", "skipped", "error", "done"]
    value: object | None = None
    confidence: float | None = None


class FillComplete(BaseModel):
    type: Literal["FILL_COMPLETE"] = "FILL_COMPLETE"
    session_id: str
    mapping: dict[str, object]


class FeedbackEventIn(BaseModel):
    field_signature: str
    language: Literal["en", "es"]
    source: Literal["local", "learned", "llm"]
    action: Literal["confirmed", "edited", "rejected"]
    suggested_hash: str
    actual_hash: str | None = None


class FeedbackBatch(BaseModel):
    type: Literal["FEEDBACK_BATCH"] = "FEEDBACK_BATCH"
    events: list[FeedbackEventIn]


class SessionCounts(BaseModel):
    resolved_local: int = 0
    resolved_backend: int = 0
    resolved_llm: int = 0
    failed: int = 0
