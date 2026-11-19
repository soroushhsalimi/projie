"""Contract tests for login (SPEC-0003 FR-1, FR-2, FR-9)."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from sara_api.modules.users.models import User


async def _register(client, payload) -> None:
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201


async def test_login_returns_token_and_cookie(client, registration_payload) -> None:
    await _register(client, registration_payload)
    client.cookies.clear()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "ali@example.com", "password": registration_payload["password"]},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]
    assert response.json()["user"]["email"] == "ali@example.com"
    assert response.cookies.get("sara_refresh")


async def test_wrong_password_and_unknown_email_are_indistinguishable(client, registration_payload) -> None:
    await _register(client, registration_payload)

    wrong = await client.post(
        "/api/v1/auth/login",
        json={"email": "ali@example.com", "password": "wrong-password-123"},
    )
    unknown = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "wrong-password-123"},
    )

    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["code"] == unknown.json()["code"] == "invalid_credentials"
    assert wrong.json()["title"] == unknown.json()["title"]
    assert wrong.json()["detail"] == unknown.json()["detail"]


async def test_login_updates_last_login_at(app, client, registration_payload) -> None:
    await _register(client, registration_payload)
    await client.post(
        "/api/v1/auth/login",
        json={"email": "ali@example.com", "password": registration_payload["password"]},
    )

    async with app.state.sessionmaker() as session:
        result = await session.execute(select(User).where(User.email == "ali@example.com"))
        user = result.scalar_one()
        assert user.last_login_at is not None


async def test_suspended_account_cannot_log_in(app, client, registration_payload) -> None:
    await _register(client, registration_payload)
    async with app.state.sessionmaker() as session:
        result = await session.execute(select(User).where(User.email == "ali@example.com"))
        user = result.scalar_one()
        user.status = "suspended"
        await session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "ali@example.com", "password": registration_payload["password"]},
    )
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"


async def test_unknown_user_never_receives_a_token(client) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": f"{uuid.uuid4().hex}@example.com", "password": "whatever-12345"},
    )
    assert response.status_code == 401
    assert "access_token" not in response.text
