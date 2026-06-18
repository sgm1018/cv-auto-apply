from typing import Literal, Optional

from pydantic import BaseModel, Field


class SettingsUpdateRequest(BaseModel):
    language: Optional[Literal["en", "es"]] = None
    autofill_mode: Optional[Literal["review", "auto"]] = None
    llm_enabled: Optional[bool] = None
    llm_provider: Optional[Literal["deepseek", "openai", "anthropic", "ollama", "custom"]] = None
    llm_model: Optional[str] = Field(default=None, max_length=120)
    llm_api_key: Optional[str] = Field(default=None, max_length=500)
    ollama_base_url: Optional[str] = None
    custom_endpoint: Optional[str] = None
    llm_daily_limit: Optional[int] = Field(default=None, ge=0, le=10000)
    notifications_enabled: Optional[bool] = None


class LLMTestRequest(BaseModel):
    api_key: Optional[str] = Field(default=None, max_length=500)
    provider: Optional[str] = None
    model: Optional[str] = Field(default=None, max_length=120)


class LLMTestResponse(BaseModel):
    ok: bool
    model: str
    message: str
