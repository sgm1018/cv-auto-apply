from pydantic import BaseModel, Field


class CVUploadResponse(BaseModel):
    cv_id: str
    parse_status: str
    filename: str
    size_bytes: int
