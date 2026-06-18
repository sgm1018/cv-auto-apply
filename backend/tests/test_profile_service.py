"""Tests for the profile service."""
import pytest

from smartcvapply.repositories.user_repository import UserRepository
from smartcvapply.services.profile_service import ProfileService


@pytest.mark.asyncio
async def test_update_creates_profile(mongo_db: None) -> None:
    user = await UserRepository().create(email="a@b.com", password_hash="x", settings={})
    p = await ProfileService().update(str(user.id), {"first_name": "Jane", "skills": ["Python"]})
    assert p.first_name == "Jane"
    assert p.skills == ["Python"]


@pytest.mark.asyncio
async def test_get_returns_profile_or_none(mongo_db: None) -> None:
    user = await UserRepository().create(email="a@b.com", password_hash="x", settings={})
    assert await ProfileService().get(str(user.id)) is None
    await ProfileService().update(str(user.id), {"first_name": "Jane"})
    p = await ProfileService().get(str(user.id))
    assert p is not None
    assert p.first_name == "Jane"
