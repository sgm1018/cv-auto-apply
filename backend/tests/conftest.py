"""Test fixtures: in-memory Mongo, settings, app client."""
import asyncio
import os
from typing import AsyncIterator

import pytest
import pytest_asyncio
from mongomock_motor import AsyncMongoMockClient

from smartcvapply.core.config import get_settings
from smartcvapply.core.db import init_beanie
from smartcvapply.models import CV, FeedbackEvent, FillSession, LearnedMapping, Profile, User


@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("MONGO_URI", "mongodb://test")
    monkeypatch.setenv("MONGO_DB", "smartcvapply_test")
    monkeypatch.setenv("JWT_SECRET", "x" * 32)
    monkeypatch.setenv("FERNET_KEY", "jYbqgCuMy004d4KbFRAcSRtwg8ImpLefLABtUlF_AaU=")
    monkeypatch.setenv("CV_MASTER_KEY", "a" * 32)
    monkeypatch.setenv("S3_ENDPOINT_URL", "http://test:9000")
    monkeypatch.setenv("S3_ACCESS_KEY", "x")
    monkeypatch.setenv("S3_SECRET_KEY", "x")
    monkeypatch.setenv("S3_BUCKET", "test")
    get_settings.cache_clear()


@pytest_asyncio.fixture
async def mongo_db() -> AsyncIterator[None]:
    client = AsyncMongoMockClient()
    await init_beanie(
        client, db_name="smartcvapply_test",
        document_models=[User, Profile, CV, LearnedMapping, FillSession, FeedbackEvent],
    )
    yield
    client.close()
