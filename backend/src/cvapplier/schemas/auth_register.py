from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    language: str = Field(default="en", pattern="^(en|es)$")
    consent_terms: bool
    consent_llm: bool = True


class RegisterResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: str
