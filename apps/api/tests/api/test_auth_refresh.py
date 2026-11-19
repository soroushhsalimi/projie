"""Contract tests for refresh rotation, reuse detection and logout (SPEC-0003 FR-3..FR-5)."""

from __future__ import annotations

from datetime import timedelta

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from sara_api.core.security import hash_refresh_token
from sara_api.modules.users.models import RefreshToken


async def _register(client, payload) -> str:
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    token = response.cookies.get("sara_refresh")
    assert token
    return token


def _cookie_client(app, token: str) -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
        headers={"Cookie": f"sara_refresh={token}"},
    )


async def test_refresh_rotates_cookie_and_revokes_old_token(
    app, client, registration_payload
) -> None:
    old = await _register(client, registration_payload)

    response = await client.post("/api/v1/auth/refresh")

    assert response.status_code == 200
    new = response.cookies.get("sara_refresh")
    assert new and new != old
    assert response.json()["access_token"]

    async with app.state.sessionmaker() as session:
        result = await session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(old))
        )
        old_row = result.scalar_one()
    assert old_row.revoked_at is not None
    assert old_row.replaced_by is not None


async def test_replay_of_rotated_token_revokes_the_family(app, client, registration_payload) -> None:
    old = await _register(client, registration_payload)
    rotated = await client.post("/api/v1/auth/refresh")
    new = rotated.cookies.get("sara_refresh")
    assert new

    async with _cookie_client(app, old) as replay:
        replay_response = await replay.post("/api/v1/auth/refresh")

    assert replay_response.status_code == 401
    assert replay_response.json()["code"] == "invalid_session"

    async with _cookie_client(app, new) as after_reuse:
        family_response = await after_reuse.post("/api/v1/auth/refresh")

    assert family_response.status_code == 401


async def test_refresh_without_cookie_is_401(client) -> None:
    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_session"


async def test_expired_refresh_token_is_rejected_and_family_revoked(
    app, client, registration_payload
) -> None:
    token = await _register(client, registration_payload)

    async with app.state.sessionmaker() as session:
        result = await session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(token))
        )
        row = result.scalar_one()
        row.expires_at = row.issued_at - timedelta(days=1)
        await session.commit()

    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_session"


async def test_refresh_rejects_untrusted_origin(app, client, registration_payload) -> None:
    token = await _register(client, registration_payload)
    client.cookies.clear()

    async with _cookie_client(app, token) as same_origin:
        blocked = await same_origin.post(
            "/api/v1/auth/refresh", headers={"Origin": "https://evil.example"}
        )
        allowed = await same_origin.post(
            "/api/v1/auth/refresh", headers={"Origin": "http://localhost:5173"}
        )

    assert blocked.status_code == 403
    assert blocked.json()["code"] == "origin_not_allowed"
    assert allowed.status_code == 200


async def test_logout_revokes_session_and_clears_cookie(client, registration_payload) -> None:
    token = await _register(client, registration_payload)

    response = await client.post("/api/v1/auth/logout")

    assert response.status_code == 204
    assert "max-age=0" in response.headers["set-cookie"].lower()

    async with _cookie_client(client._transport.app, token) as replay:  # type: ignore[attr-defined]
        refresh = await replay.post("/api/v1/auth/refresh")

    assert refresh.status_code == 401


async def test_logout_without_cookie_is_idempotent(client) -> None:
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 204
