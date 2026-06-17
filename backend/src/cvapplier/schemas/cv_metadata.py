from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class CVMetadata(BaseModel):
    cv_id: str
    filename: str
    mime_type: str
    size_bytes: int
    is_primary: bool
    parse_status: str
    parsed_data: Optional[dict[str, Any]] = None
    parse_error: Optional[str] = None
    uploaded_at: datetime
    parsed_at: Optional[datetime] = None
