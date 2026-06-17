"""Tests for the settings service (encrypted API key handling)."""
import pytest

from cvapplier.core.exceptions import ValidationFailed
from cvapplier.repositories.user_repository import UserRepository
from cvapplier.services.settings_service import SettingsService


@pytest.mark.asyncio
async def test_get_returns_defaults(mongo_db: None) -> None:
    user = await UserRepository().create(email="a@b.com", password_hash="x", settings={})
    out = await SettingsService().get(user)
    assert out["llm_provider"] == "deepseek"
    assert out["llm_model"] == "deepseek-v4-flash"
    assert out["llm_api_key_set"] is False


@pytest.mark.asyncio
async def test_update_encrypts_api_key(mongo_db: None) -> None:
    user = await UserRepository().create(email="a@b.com", password_hash="x", settings={})
    out = await SettingsService().update(user, {"llm_api_key": "sk-secret"})
    assert out["llm_api_key_set"] is True
    raw = await UserRepository().get_by_id(str(user.id))
    assert raw is not None
    assert raw.settings["llm_api_key_enc"] != "sk-secret"
    assert SettingsService().decrypt_api_key(raw) == "sk-secret"


@pytest.mark.asyncio
async def test_update_rejects_invalid_model(mongo_db: None) -> None:
    user = await UserRepository().create(email="a@b.com", password_hash="x", settings={})
    with pytest.raises(ValidationFailed):
        await SettingsService().update(user, {
            "llm_provider": "deepseek", "llm_model": "totally-fake",
        })


@pytest.mark.asyncio
async def test_update_clears_api_key(mongo_db: None) -> None:
    user = await UserRepository().create(email="a@b.com", password_hash="x", settings={})
    await SettingsService().update(user, {"llm_api_key": "sk-secret"})
    out = await SettingsService().update(user, {"llm_api_key": ""})
    assert out["llm_api_key_set"] is False
