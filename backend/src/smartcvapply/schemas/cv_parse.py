"""CV parse response schema."""
from typing import Any

from pydantic import BaseModel, Field


class CVParseResponse(BaseModel):
    cv_id: str
    parse_status: str
    parsed_data: dict[str, Any] | None = None
    parse_error: str | None = None
