from typing import Literal, Optional

from pydantic import BaseModel, Field


class SettingsResponse(BaseModel):
    language: Literal["en", "es"]
    autofill_mode: Literal["review", "auto"]
    llm_enabled: bool
    llm_provider: Literal["deepseek", "openai", "anthropic", "ollama", "custom"]
    llm_model: str
    llm_api_key_set: bool
    ollama_base_url: Optional[str] = None
    custom_endpoint: Optional[str] = None
    llm_daily_limit: int
    notifications_enabled: bool
