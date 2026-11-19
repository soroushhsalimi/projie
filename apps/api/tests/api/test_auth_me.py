"""Contract tests for the current-principal endpoint (SPEC-0003 FR-6, FR-7)."""

from __future__ import annotations

import uuid
from datetime import timedelta

import jwt
from sqlalchemy import select

from sara_api.core.security import utcnow
from sara_api.modules.users.models import User


async def _register(client, payload) -> str:
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    return response.json()["access_token"]


async def test_me_requires_bearer(client) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_token"
    assert response.headers["www-authenticate"] == "Bearer"


async def test_me_returns_public_profile(client, registration_payload) -> None:
    token = await _register(client, registration_payload)

    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "ali@example.com"
    assert body["role"] == "user"
    assert "password_hash" not in body


async def test_me_rejects_a_refresh_typed_token(client) -> None:
    now = utcnow()
    token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "role": "user",
            "typ": "refresh",
            "iss": "sara",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
        },
        "test-secret-key-0123456789abcdef0123456789abcdef",
        algorithm="HS256",
    )

    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401


async def test_me_rejects_inactive_account(app, client, registration_payload) -> None:
    token = await _register(client, registration_payload)
    async with app.state.sessionmaker() as session:
        result = await session.execute(select(User).where(User.email == "ali@example.com"))
        user = result.scalar_one()
        user.status = "suspended"
        await session.commit()

    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
