"""API contract tests for the accommodation review queue (SPEC-0006 FR-1…FR-6)."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select

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
    "note": None,
}


async def _register(client, email: str, full_name: str) -> str:  # type: ignore[no-untyped-def]
    response = await client.post(
        "/api/v1/auth/register",
        json={"full_name": full_name, "email": email, "password": PASSWORD},
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


async def _set_role(app, email: str, role: str) -> None:  # type: ignore[no-untyped-def]
    async with app.state.sessionmaker() as session:
        user = (await session.execute(select(User).where(User.email == email))).scalar_one()
        user.role = role
        await session.commit()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _submit(client, token: str, **overrides) -> str:  # type: ignore[no-untyped-def]
    response = await client.post(
        "/api/v1/requests", headers=_auth(token), json={**PAYLOAD, **overrides}
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _manager(client, app) -> str:  # type: ignore[no-untyped-def]
    token = await _register(client, MANAGER, "رضا کریمی")
    await _set_role(app, MANAGER, "manager")
    return token


async def test_queue_requires_authentication(client) -> None:
    response = await client.get("/api/v1/requests/queue")
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_token"


async def test_queue_rejects_a_resident(client) -> None:
    token = await _register(client, RESIDENT, "سارا محمدی")

    response = await client.get("/api/v1/requests/queue", headers=_auth(token))

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


async def test_queue_lists_every_resident_with_the_applicant_name(client, app) -> None:
    resident = await _register(client, RESIDENT, "سارا محمدی")
    neighbour = await _register(client, NEIGHBOUR, "مینا رضایی")
    await _submit(client, resident, dormitory_name="خوابگاه الزهرا")
    await _submit(client, neighbour, dormitory_name="خوابگاه کوثر")
    token = await _manager(client, app)

    response = await client.get("/api/v1/requests/queue", headers=_auth(token))

    assert response.status_code == 200
    body = response.json()
    assert {item["dormitory_name"] for item in body["items"]} == {
        "خوابگاه الزهرا",
        "خوابگاه کوثر",
    }
    assert {item["applicant_name"] for item in body["items"]} == {"سارا محمدی", "مینا رضایی"}
    assert body["meta"] == {"page": 1, "per_page": 20, "total": 2}


async def test_queue_filters_by_status(client, app) -> None:
    resident = await _register(client, RESIDENT, "سارا محمدی")
    first = await _submit(client, resident)
    token = await _manager(client, app)
    await client.patch(
        f"/api/v1/requests/{first}/status", headers=_auth(token), json={"status": "under_review"}
    )
    neighbour = await _register(client, NEIGHBOUR, "مینا رضایی")
    await _submit(client, neighbour)

    under_review = await client.get(
        "/api/v1/requests/queue?status=under_review", headers=_auth(token)
    )
    submitted = await client.get(
        "/api/v1/requests/queue?status=submitted", headers=_auth(token)
    )

    assert under_review.status_code == 200
    assert [item["id"] for item in under_review.json()["items"]] == [first]
    assert under_review.json()["meta"]["total"] == 1
    assert [item["applicant_name"] for item in submitted.json()["items"]] == ["مینا رضایی"]


async def test_queue_paginates(client, app) -> None:
    resident = await _register(client, RESIDENT, "سارا محمدی")
    neighbour = await _register(client, NEIGHBOUR, "مینا رضایی")
    await _submit(client, resident)
    await _submit(client, neighbour)
    token = await _manager(client, app)

    first_page = await client.get(
        "/api/v1/requests/queue?page=1&per_page=1", headers=_auth(token)
    )

    assert len(first_page.json()["items"]) == 1
    assert first_page.json()["meta"] == {"page": 1, "per_page": 1, "total": 2}


async def test_queue_rejects_an_unknown_status_filter(client, app) -> None:
    token = await _manager(client, app)

    response = await client.get("/api/v1/requests/queue?status=archived", headers=_auth(token))

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


async def test_queue_rejects_an_oversized_page_size(client, app) -> None:
    token = await _manager(client, app)

    response = await client.get("/api/v1/requests/queue?per_page=500", headers=_auth(token))

    assert response.status_code == 422


async def test_status_changes_follow_the_state_machine(client, app) -> None:
    resident = await _register(client, RESIDENT, "سارا محمدی")
    request_id = await _submit(client, resident)
    token = await _manager(client, app)

    under_review = await client.patch(
        f"/api/v1/requests/{request_id}/status",
        headers=_auth(token),
        json={"status": "under_review"},
    )
    assert under_review.status_code == 200
    assert under_review.json()["status"] == "under_review"
    assert under_review.json()["applicant_name"] == "سارا محمدی"

    approved = await client.patch(
        f"/api/v1/requests/{request_id}/status",
        headers=_auth(token),
        json={"status": "approved"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    repeated = await client.patch(
        f"/api/v1/requests/{request_id}/status",
        headers=_auth(token),
        json={"status": "rejected"},
    )
    assert repeated.status_code == 409
    assert repeated.json()["code"] == "request_transition_not_allowed"


async def test_review_rejects_an_unknown_or_non_review_target(client, app) -> None:
    resident = await _register(client, RESIDENT, "سارا محمدی")
    request_id = await _submit(client, resident)
    token = await _manager(client, app)

    response = await client.patch(
        f"/api/v1/requests/{request_id}/status",
        headers=_auth(token),
        json={"status": "archived"},
    )
    submitted = await client.patch(
        f"/api/v1/requests/{request_id}/status",
        headers=_auth(token),
        json={"status": "submitted"},
    )

    assert response.status_code == 422
    assert submitted.status_code == 422


async def test_review_of_an_unknown_request_is_404(client, app) -> None:
    token = await _manager(client, app)

    response = await client.patch(
        f"/api/v1/requests/{uuid4()}/status",
        headers=_auth(token),
        json={"status": "approved"},
    )

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


async def test_a_resident_cannot_change_a_status(client, app) -> None:
    resident = await _register(client, RESIDENT, "سارا محمدی")
    request_id = await _submit(client, resident)

    response = await client.patch(
        f"/api/v1/requests/{request_id}/status",
        headers=_auth(resident),
        json={"status": "approved"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


async def test_a_request_under_review_still_blocks_a_new_submission(client, app) -> None:
    resident = await _register(client, RESIDENT, "سارا محمدی")
    request_id = await _submit(client, resident)
    token = await _manager(client, app)
    await client.patch(
        f"/api/v1/requests/{request_id}/status",
        headers=_auth(token),
        json={"status": "under_review"},
    )

    second = await client.post("/api/v1/requests", headers=_auth(resident), json=PAYLOAD)

    assert second.status_code == 409
    assert second.json()["code"] == "request_already_active"
