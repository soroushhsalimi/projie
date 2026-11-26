"""Shared test fixtures: isolated app, isolated database, HTTP client and factories."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from sara_api.core.config import Settings
from sara_api.db.base import Base
from sara_api.main import create_app


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        environment="test",
        database_url=f"sqlite+aiosqlite:///{(tmp_path / 'test.db').as_posix()}",
        secret_key="test-secret-key-0123456789abcdef0123456789abcdef",
        cookie_secure=False,
        auto_create_schema=False,
        cors_origins=["http://localhost:5173"],
    )


@pytest_asyncio.fixture
async def app(settings: Settings):
    application = create_app(settings)
    async with application.state.engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield application
    await application.state.engine.dispose()


@pytest_asyncio.fixture
async def client(app) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


@pytest.fixture
def registration_payload() -> dict[str, str]:
    return {
        "full_name": "علی رضایی",
        "email": "ali@example.com",
        "password": "CorrectHorseBatteryStaple",
        "national_id": "0012345679",
        "phone": "+989121234567",
        "address": "تهران، خیابان آزادی، پلاک ۱۲",
    }
