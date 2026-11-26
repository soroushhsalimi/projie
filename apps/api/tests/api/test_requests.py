"""API contract tests for accommodation requests (SPEC-0005 FR-1…FR-8)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from helpers import registration_body
from sara_api.modules.users.models import User

PASSWORD = "CorrectHorseBatteryStaple"
RESIDENT = "resident@example.com"
NEIGHBOUR = "neighbour@example.com"
MANAGER = "manager@example.com"

PAYLOAD = {
    "dormitory_name": "خوابگاه الزهرا",
    "room_type": "double",
    "desired_move_in": "2027-02-01",
    "duration_months": 6,
    "note": "اتاق نزدیک پنجره ترجیح داده می‌شود.",
}


async def _register(client, email: str, full_name: str) -> str:  # type: ignore[no-untyped-def]
    response = await client.post(
        "/api/v1/auth/register", json=registration_body(email, full_name, PASSWORD)
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


async def _set_role(app, email: str, role: str) -> None:  # type: ignore[no-untyped-def]
    async with app.state.sessionmaker() as session:
        user = (await session.execute(select(User).where(User.email == email))).scalar_one()
        user.role = role
        await session.commit()


async def _id_of(app, email: str) -> UUID:  # type: ignore[no-untyped-def]
    async with app.state.sessionmaker() as session:
        return (await session.execute(select(User.id).where(User.email == email))).scalar_one()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_create_requires_authentication(client) -> None:
    response = await client.post("/api/v1/requests", json=PAYLOAD)
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_token"


async def test_create_returns_201_with_a_submitted_request(client) -> None:
    token = await _register(client, RESIDENT, "سارا محمدی")

    response = await client.post("/api/v1/requests", headers=_auth(token), json=PAYLOAD)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "submitted"
    assert body["dormitory_name"] == PAYLOAD["dormitory_name"]
    assert body["room_type"] == "double"
    assert body["duration_months"] == 6
    assert body["desired_move_in"] == "2027-02-01"
    assert body["created_at"].endswith("Z")


async def test_second_active_request_is_rejected(client) -> None:
    token = await _register(client, RESIDENT, "سارا محمدی")
    first = await client.post("/api/v1/requests", headers=_auth(token), json=PAYLOAD)
    assert first.status_code == 201

    second = await client.post("/api/v1/requests", headers=_auth(token), json=PAYLOAD)

    assert second.status_code == 409
    assert second.json()["code"] == "request_already_active"
    listing = await client.get("/api/v1/requests", headers=_auth(token))
    assert listing.json()["meta"]["total"] == 1


async def test_list_returns_only_the_callers_requests(client) -> None:
    resident = await _register(client, RESIDENT, "سارا محمدی")
    neighbour = await _register(client, NEIGHBOUR, "مینا رضایی")
    await client.post("/api/v1/requests", headers=_auth(resident), json=PAYLOAD)
    await client.post(
        "/api/v1/requests",
        headers=_auth(neighbour),
        json={**PAYLOAD, "dormitory_name": "خوابگاه کوثر"},
    )

    response = await client.get("/api/v1/requests", headers=_auth(resident))

    assert response.status_code == 200
    body = response.json()
    assert [item["dormitory_name"] for item in body["items"]] == [PAYLOAD["dormitory_name"]]
    assert body["meta"] == {"page": 1, "per_page": 20, "total": 1}


async def test_withdraw_changes_the_status_once(client) -> None:
    token = await _register(client, RESIDENT, "سارا محمدی")
    created = await client.post("/api/v1/requests", headers=_auth(token), json=PAYLOAD)
    request_id = created.json()["id"]

    withdrawn = await client.post(
        f"/api/v1/requests/{request_id}/withdraw", headers=_auth(token)
    )

    assert withdrawn.status_code == 200
    assert withdrawn.json()["status"] == "withdrawn"

    repeated = await client.post(
        f"/api/v1/requests/{request_id}/withdraw", headers=_auth(token)
    )
    assert repeated.status_code == 409
    assert repeated.json()["code"] == "request_not_withdrawable"


async def test_withdrawing_a_foreign_request_is_404(client) -> None:
    resident = await _register(client, RESIDENT, "سارا محمدی")
    neighbour = await _register(client, NEIGHBOUR, "مینا رضایی")
    created = await client.post("/api/v1/requests", headers=_auth(neighbour), json=PAYLOAD)

    response = await client.post(
        f"/api/v1/requests/{created.json()['id']}/withdraw", headers=_auth(resident)
    )

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


async def test_manager_and_admin_are_forbidden(client, app) -> None:
    manager_token = await _register(client, MANAGER, "رضا کریمی")
    await _set_role(app, MANAGER, "manager")

    listing = await client.get("/api/v1/requests", headers=_auth(manager_token))
    create = await client.post("/api/v1/requests", headers=_auth(manager_token), json=PAYLOAD)

    assert listing.status_code == 403
    assert listing.json()["code"] == "forbidden"
    assert create.status_code == 403


async def test_invalid_payloads_are_422(client) -> None:
    token = await _register(client, RESIDENT, "سارا محمدی")

    blank_dormitory = await client.post(
        "/api/v1/requests", headers=_auth(token), json={**PAYLOAD, "dormitory_name": "   "}
    )
    bad_duration = await client.post(
        "/api/v1/requests", headers=_auth(token), json={**PAYLOAD, "duration_months": 0}
    )
    unknown_room = await client.post(
        "/api/v1/requests", headers=_auth(token), json={**PAYLOAD, "room_type": "suite"}
    )

    assert blank_dormitory.status_code == 422
    assert blank_dormitory.json()["code"] == "validation_error"
    assert bad_duration.status_code == 422
    assert unknown_room.status_code == 422
