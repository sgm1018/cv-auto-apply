from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CVMetadata(BaseModel):
    cv_id: str
    filename: str
    mime_type: str
    size_bytes: int
    is_primary: bool
    parse_status: str
    parse_error: Optional[str] = None
    uploaded_at: datetime
    parsed_at: Optional[datetime] = None
