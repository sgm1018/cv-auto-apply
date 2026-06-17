from typing import Literal

from pydantic import BaseModel


class FeedbackEventIn(BaseModel):
    field_signature: str
    language: Literal["en", "es"]
    source: Literal["local", "learned", "llm"]
    action: Literal["confirmed", "edited", "rejected"]
    suggested_hash: str
    actual_hash: str | None = None


class FeedbackBatchRequest(BaseModel):
    events: list[FeedbackEventIn]


class FeedbackBatchResponse(BaseModel):
    accepted: int
