"""Tests for the auth service."""
import pytest

from smartcvapply.core.exceptions import AuthError
from smartcvapply.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_register_creates_user(mongo_db: None) -> None:
    res = await AuthService().register("a@b.com", "super-secret-password-123", language="en")
    assert res.user.email == "a@b.com"
    assert res.access_token
    assert res.refresh_token


@pytest.mark.asyncio
async def test_register_rejects_duplicate(mongo_db: None) -> None:
    await AuthService().register("a@b.com", "super-secret-password-123", language="en")
    with pytest.raises(AuthError):
        await AuthService().register("a@b.com", "super-secret-password-123", language="en")


@pytest.mark.asyncio
async def test_register_rejects_short_password(mongo_db: None) -> None:
    with pytest.raises(AuthError):
        await AuthService().register("a@b.com", "short", language="en")


@pytest.mark.asyncio
async def test_login_success(mongo_db: None) -> None:
    await AuthService().register("a@b.com", "super-secret-password-123", language="en")
    res = await AuthService().login("a@b.com", "super-secret-password-123")
    assert res.access_token


@pytest.mark.asyncio
async def test_login_wrong_password(mongo_db: None) -> None:
    await AuthService().register("a@b.com", "super-secret-password-123", language="en")
    with pytest.raises(AuthError):
        await AuthService().login("a@b.com", "wrong-password-456")


@pytest.mark.asyncio
async def test_refresh_rotates(mongo_db: None) -> None:
    reg = await AuthService().register("a@b.com", "super-secret-password-123", language="en")
    refreshed = await AuthService().refresh(reg.refresh_token)
    assert refreshed.refresh_token != reg.refresh_token


@pytest.mark.asyncio
async def test_refresh_reuse_revokes(mongo_db: None) -> None:
    reg = await AuthService().register("a@b.com", "super-secret-password-123", language="en")
    await AuthService().refresh(reg.refresh_token)
    with pytest.raises(AuthError):
        await AuthService().refresh(reg.refresh_token)
