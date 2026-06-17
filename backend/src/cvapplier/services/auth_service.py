"""Auth use cases: register, login, refresh rotation, logout."""
from dataclasses import dataclass

from jose import JWTError

from cvapplier.core.config import get_settings
from cvapplier.core.exceptions import AuthError
from cvapplier.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from cvapplier.models.user import User
from cvapplier.repositories.user_repository import UserRepository


@dataclass
class AuthResult:
    user: User
    access_token: str
    refresh_token: str


def default_settings() -> dict:
    return {
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


class AuthService:
    MIN_PASSWORD_LEN = 12

    def __init__(self, repo: UserRepository | None = None) -> None:
        self.repo = repo or UserRepository()
        self.s = get_settings()

    async def register(self, email: str, password: str, *, language: str) -> AuthResult:
        if len(password) < self.MIN_PASSWORD_LEN:
            raise AuthError(f"Password must be at least {self.MIN_PASSWORD_LEN} characters")
        if await self.repo.get_by_email(email):
            raise AuthError("Email already registered")
        settings = {**default_settings(), "language": language}
        user = await self.repo.create(
            email=email, password_hash=hash_password(password), settings=settings,
        )
        return await self._issue(user)

    async def login(self, email: str, password: str) -> AuthResult:
        user = await self.repo.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise AuthError("Invalid credentials")
        await self.repo.set_last_login(str(user.id))
        return await self._issue(user)

    async def refresh(self, refresh_token: str) -> AuthResult:
        try:
            payload = decode_token(refresh_token, secret=self.s.jwt_secret)
        except JWTError as e:
            raise AuthError("Invalid refresh token") from e
        if payload.get("type") != "refresh":
            raise AuthError("Not a refresh token")
        user = await self.repo.get_by_id(payload["sub"])
        if user is None or user.refresh_token_hash != hash_refresh_token(refresh_token):
            if user is not None:
                await self.repo.set_refresh_hash(str(user.id), None)
            raise AuthError("Refresh token reuse detected")
        return await self._issue(user)

    async def logout(self, user_id: str) -> None:
        await self.repo.set_refresh_hash(user_id, None)

    async def _issue(self, user: User) -> AuthResult:
        access = create_access_token(
            str(user.id), user.email,
            secret=self.s.jwt_secret, ttl_min=self.s.access_token_ttl_min,
        )
        refresh = create_refresh_token(
            str(user.id), secret=self.s.jwt_secret, ttl_days=self.s.refresh_token_ttl_days,
        )
        await self.repo.set_refresh_hash(str(user.id), hash_refresh_token(refresh))
        return AuthResult(user=user, access_token=access, refresh_token=refresh)
