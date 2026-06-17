"""CV document."""
from datetime import datetime
from typing import Annotated, Any, Literal

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field

from cvapplier.utils.time import utcnow


class CV(Document):
    user_id: Annotated[PydanticObjectId, Indexed()]
    file_id: str
    filename: str
    mime_type: str
    size_bytes: int
    is_primary: bool = False
    parse_status: Literal["pending", "processing", "done", "failed"] = "pending"
    parsed_data: dict[str, Any] | None = None
    parse_error: str | None = None
    uploaded_at: datetime = Field(default_factory=utcnow)
    parsed_at: datetime | None = None

    class Settings:
        name = "cvs"
        use_state_management = True
        indexes = [[("user_id", 1), ("is_primary", 1)]]
