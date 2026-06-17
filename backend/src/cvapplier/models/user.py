"""User document."""
from datetime import datetime
from typing import Annotated, Any

from beanie import Document, Indexed
from pydantic import EmailStr, Field

from cvapplier.utils.time import utcnow


class User(Document):
    email: Annotated[EmailStr, Indexed(unique=True)]  # type: ignore[valid-type]
    password_hash: str
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    email_verified: bool = False
    last_login: datetime | None = None
    refresh_token_hash: str | None = None
    consents: list[dict[str, Any]] = Field(default_factory=list)

    settings: dict[str, Any] = Field(
        default_factory=lambda: {
            "language": "en",
            "autofill_mode": "review",
            "llm_enabled": True,
            "llm_provider": "deepseek",
            "llm_model": "deepseek-chat",
            "llm_api_key_enc": None,
            "ollama_base_url": None,
            "custom_endpoint": None,
            "llm_daily_limit": 100,
            "notifications_enabled": True,
        }
    )

    class Settings:
        name = "users"
        use_state_management = True
