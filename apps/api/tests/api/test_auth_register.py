"""Contract tests for public registration (SPEC-0002)."""

from __future__ import annotations

from sqlalchemy import select

from sara_api.modules.users.models import User


async def _load_user(app, email: str) -> User | None:
    async with app.state.sessionmaker() as session:
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()


async def test_register_returns_201_and_sets_refresh_cookie(client, registration_payload) -> None:
    response = await client.post("/api/v1/auth/register", json=registration_payload)

    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 900
    assert body["user"]["email"] == "ali@example.com"
    assert body["user"]["role"] == "user"
    assert body["user"]["status"] == "active"
    assert body["user"]["national_id"] == "0012345679"
    assert body["user"]["phone"] == "09121234567"
    assert body["user"]["address"] == "تهران، خیابان آزادی، پلاک ۱۲"
    assert body["user"]["created_at"].endswith("Z")
    assert "password" not in body["user"]

    set_cookie = response.headers["set-cookie"].lower()
    assert "httponly" in set_cookie
    assert "path=/api/v1/auth" in set_cookie
    assert "samesite=lax" in set_cookie
    assert response.cookies.get("sara_refresh")


async def test_duplicate_email_is_case_insensitive_and_returns_409(client, registration_payload) -> None:
    await client.post("/api/v1/auth/register", json=registration_payload)
    duplicate = {**registration_payload, "email": "ALI@Example.com"}

    response = await client.post("/api/v1/auth/register", json=duplicate)

    assert response.status_code == 409
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "email_already_registered"


async def test_short_password_returns_422_with_field_pointer(client, registration_payload) -> None:
    response = await client.post(
        "/api/v1/auth/register", json={**registration_payload, "password": "short"}
    )

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"
    assert any(item["field"] == "password" for item in body["errors"])


async def test_client_supplied_role_is_rejected(client, registration_payload) -> None:
    response = await client.post(
        "/api/v1/auth/register", json={**registration_payload, "role": "admin"}
    )

    assert response.status_code == 422
    assert await _load_user(client._transport.app, "ali@example.com") is None  # type: ignore[attr-defined]


async def test_password_is_argon2id_and_never_serialized(app, client, registration_payload) -> None:
    response = await client.post("/api/v1/auth/register", json=registration_payload)
    assert response.status_code == 201
    assert "CorrectHorseBatteryStaple" not in response.text

    user = await _load_user(app, "ali@example.com")
    assert user is not None
    assert user.password_hash.startswith("$argon2id$")
    assert user.password_hash != registration_payload["password"]


async def test_identity_fields_are_required(client, registration_payload) -> None:
    payload = {
        key: value
        for key, value in registration_payload.items()
        if key not in {"national_id", "phone", "address"}
    }

    response = await client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"
    assert {"national_id", "phone", "address"} <= {
        item["field"] for item in body["errors"]
    }


async def test_invalid_national_id_and_mobile_are_422(client, registration_payload) -> None:
    bad_national_id = await client.post(
        "/api/v1/auth/register", json={**registration_payload, "national_id": "12345"}
    )
    bad_mobile = await client.post(
        "/api/v1/auth/register", json={**registration_payload, "phone": "02112345678"}
    )

    assert bad_national_id.status_code == 422
    assert any(item["field"] == "national_id" for item in bad_national_id.json()["errors"])
    assert bad_mobile.status_code == 422
    assert any(item["field"] == "phone" for item in bad_mobile.json()["errors"])


async def test_national_id_and_mobile_are_normalized(client, registration_payload) -> None:
    payload = {
        **registration_payload,
        "national_id": "۰۰۱۲۳۴۵۶۷۹",
        "phone": "+98 912 123 4567",
    }

    response = await client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 201
    assert response.json()["user"]["national_id"] == "0012345679"
    assert response.json()["user"]["phone"] == "09121234567"


async def test_duplicate_national_id_returns_409(client, registration_payload) -> None:
    first = await client.post("/api/v1/auth/register", json=registration_payload)
    assert first.status_code == 201

    response = await client.post(
        "/api/v1/auth/register",
        json={**registration_payload, "email": "other@example.com"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "national_id_already_registered"


async def test_full_name_is_trimmed(client, registration_payload) -> None:
    response = await client.post(
        "/api/v1/auth/register", json={**registration_payload, "full_name": "  علی رضایی  "}
    )
    assert response.status_code == 201
    assert response.json()["user"]["full_name"] == "علی رضایی"
