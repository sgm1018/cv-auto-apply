from pydantic import BaseModel, EmailStr


class MeResponse(BaseModel):
    user_id: str
    email: EmailStr
    language: str
    llm_provider: str
    llm_model: str
    llm_enabled: bool
