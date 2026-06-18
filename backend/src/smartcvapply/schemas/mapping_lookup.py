from pydantic import BaseModel, Field


class LearnedMappingDTO(BaseModel):
    field_signature: str
    target_path: str
    transform: str | None = None
    confidence: float
    usage_count: int


class LearnedLookupResponse(BaseModel):
    mappings: dict[str, LearnedMappingDTO] = Field(default_factory=dict)
