"""Contract tests for liveness and readiness (SPEC-0001 FR-1, FR-2)."""

from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from sara_api.core.config import Settings
from sara_api.main import create_app


async def test_liveness_is_200(client) -> None:
    response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_readiness_checks_database(client) -> None:
    response = await client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "ok",
        "version": response.json()["version"],
    }


async def test_readiness_returns_503_when_database_is_unreachable(tmp_path) -> None:
    settings = Settings(
        environment="test",
        database_url=f"sqlite+aiosqlite:///{(tmp_path / 'missing' / 'nope.db').as_posix()}",
        secret_key="x" * 48,
        auto_create_schema=False,
    )
    app = create_app(settings)
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        live = await client.get("/health/live")
        ready = await client.get("/health/ready")
    await app.state.engine.dispose()

    assert live.status_code == 200
    assert ready.status_code == 503
    assert ready.headers["content-type"].startswith("application/problem+json")
    assert ready.json()["code"] == "not_ready"
