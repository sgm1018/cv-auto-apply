"""FastAPI dependencies."""
from typing import Annotated

from fastapi import Depends, Header
from jose import JWTError

from cvapplier.core.config import Settings, get_settings
from cvapplier.core.exceptions import AuthError
from cvapplier.core.security import decode_token
from cvapplier.models.user import User
from cvapplier.repositories.user_repository import UserRepository


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    settings: Annotated[Settings, Depends(get_settings)] = None,
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthError("Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token, secret=settings.jwt_secret)
    except JWTError as e:
        raise AuthError("Invalid token") from e
    if payload.get("type") != "access":
        raise AuthError("Not an access token")
    user = await UserRepository().get_by_id(payload["sub"])
    if user is None:
        raise AuthError("User not found")
    return user
