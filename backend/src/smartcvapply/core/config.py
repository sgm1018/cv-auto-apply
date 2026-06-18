"""Application configuration loaded from environment variables."""
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: Literal["development", "staging", "production"] = "development"
    log_level: str = "info"

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "smartcvapply"

    s3_endpoint_url: str = "http://localhost:9000"
    s3_region: str = "us-east-1"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "smartcvapply-cvs"
    s3_use_ssl: bool = False

    jwt_secret: str = Field(default="dev-secret-please-change-32+chars", min_length=16)
    jwt_algorithm: str = "HS256"
    access_token_ttl_min: int = 15
    refresh_token_ttl_days: int = 30
    fernet_key: str = Field(default="", min_length=44)
    cv_master_key: str = Field(default="a" * 32, min_length=16)

    cors_allowed_origins: str = "http://localhost:5173"
    public_url: str = ""
    sentry_dsn: str = ""

    @field_validator("cors_allowed_origins")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
