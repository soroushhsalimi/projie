"""API contract tests for the guest desk (SPEC-0008 FR-1…FR-7)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from helpers import registration_body
from sara_api.modules.guests import service as guest_service
from sara_api.modules.guests.models import GuestVisit
from sara_api.modules.users.models import User

PASSWORD = "CorrectHorseBatteryStaple"
BASE = datetime(2026, 11, 26, 16, 0, tzinfo=UTC)
WINDOW_END = BASE + timedelta(hours=2)
RESIDENT = "resident@example.com"
MANAGER = "manager@example.com"


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


async def _manager(client, app) -> str:  # type: ignore[no-untyped-def]
    token = await _register(client, MANAGER, "رضا کریمی")
    await _set_role(app, MANAGER, "manager")
    return token


async def _visit(  # type: ignore[no-untyped-def]
    app,
    host_id: UUID,
    *,
    guest_name: str,
    status: str = "expected",
    created_at: datetime = BASE,
    allowed_from: datetime = BASE,
    allowed_until: datetime = WINDOW_END,
    checked_in_at: datetime | None = None,
    checked_out_at: datetime | None = None,
) -> UUID:
    async with app.state.sessionmaker() as session:
        visit = GuestVisit(
            host_id=host_id,
            guest_name=guest_name,
            purpose="ملاقات",
            allowed_from=allowed_from,
            allowed_until=allowed_until,
            status=status,
            checked_in_at=checked_in_at,
            checked_out_at=checked_out_at,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add(visit)
        await session.commit()
        return visit.id


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _payload(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "guest_name": "مریم احمدی",
        "host_email": RESIDENT,
        "purpose": "ملاقات خانوادگی",
        "allowed_from": BASE.isoformat(),
        "allowed_until": WINDOW_END.isoformat(),
    }
    body.update(overrides)
    return body


@pytest.fixture
def frozen_now(monkeypatch):  # type: ignore[no-untyped-def]
    """Patch the service clock; returns a setter so each step can advance time."""
    state = {"now": BASE + timedelta(minutes=10)}
    monkeypatch.setattr(guest_service, "utcnow", lambda: state["now"])
    return state


async def test_list_requires_auth(client) -> None:
    response = await client.get("/api/v1/guests")
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_token"


async def test_list_rejects_a_resident(client) -> None:
    token = await _register(client, RESIDENT, "سارا محمدی")

    response = await client.get("/api/v1/guests", headers=_auth(token))

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


async def test_list_filters_by_status_and_paginates(client, app) -> None:
    await _register(client, RESIDENT, "سارا محمدی")
    host_id = await _id_of(app, RESIDENT)
    token = await _manager(client, app)

    await _visit(app, host_id, guest_name="older expected", created_at=BASE)
    await _visit(
        app, host_id, guest_name="newer expected", created_at=BASE + timedelta(hours=1)
    )
    await _visit(
        app,
        host_id,
        guest_name="inside one",
        status="checked_in",
        created_at=BASE + timedelta(hours=2),
        checked_in_at=BASE + timedelta(hours=2),
    )

    response = await client.get("/api/v1/guests?status=expected", headers=_auth(token))

    assert response.status_code == 200
    body = response.json()
    assert [item["guest_name"] for item in body["items"]] == [
        "newer expected",
        "older expected",
    ]
    assert body["meta"] == {"page": 1, "per_page": 20, "total": 2}
    assert body["items"][0]["host_name"] == "سارا محمدی"

    second_page = await client.get(
        "/api/v1/guests?status=expected&page=2&per_page=1", headers=_auth(token)
    )
    assert [item["guest_name"] for item in second_page.json()["items"]] == ["older expected"]


async def test_list_rejects_an_unknown_status_filter(client, app) -> None:
    token = await _manager(client, app)
    response = await client.get("/api/v1/guests?status=cancelled", headers=_auth(token))
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


async def test_register_resolves_the_host_and_echoes_the_window(
    client, app, frozen_now
) -> None:
    await _register(client, RESIDENT, "سارا محمدی")
    token = await _manager(client, app)

    response = await client.post(
        "/api/v1/guests", headers=_auth(token), json=_payload()
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["guest_name"] == "مریم احمدی"
    assert body["host_name"] == "سارا محمدی"
    assert body["status"] == "expected"
    assert body["allowed_from"] == "2026-11-26T16:00:00Z"
    assert body["allowed_until"] == "2026-11-26T18:00:00Z"
    assert body["checked_in_at"] is None
    assert body["overdue"] is False


async def test_register_rejects_an_unknown_or_non_resident_host(client, app) -> None:
    token = await _manager(client, app)

    unknown = await client.post(
        "/api/v1/guests",
        headers=_auth(token),
        json=_payload(host_email="nobody@example.com"),
    )
    manager_as_host = await client.post(
        "/api/v1/guests", headers=_auth(token), json=_payload(host_email=MANAGER)
    )

    assert unknown.status_code == 422
    assert unknown.json()["code"] == "validation_error"
    assert manager_as_host.status_code == 422


async def test_register_rejects_an_invalid_window(client, app) -> None:
    await _register(client, RESIDENT, "سارا محمدی")
    token = await _manager(client, app)

    backwards = await client.post(
        "/api/v1/guests",
        headers=_auth(token),
        json=_payload(allowed_until=BASE.isoformat()),
    )
    too_long = await client.post(
        "/api/v1/guests",
        headers=_auth(token),
        json=_payload(allowed_until=(BASE + timedelta(hours=25)).isoformat()),
    )

    assert backwards.status_code == 422
    assert too_long.status_code == 422


async def test_register_rejects_a_timestamp_without_a_timezone(client, app) -> None:
    await _register(client, RESIDENT, "سارا محمدی")
    token = await _manager(client, app)

    response = await client.post(
        "/api/v1/guests",
        headers=_auth(token),
        json=_payload(allowed_from="2026-11-26T16:00:00"),
    )

    assert response.status_code == 422


async def test_check_in_is_legal_inside_the_window(client, app, frozen_now) -> None:
    await _register(client, RESIDENT, "سارا محمدی")
    host_id = await _id_of(app, RESIDENT)
    token = await _manager(client, app)
    visit_id = await _visit(app, host_id, guest_name="مریم احمدی")

    response = await client.post(
        f"/api/v1/guests/{visit_id}/check-in", headers=_auth(token)
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "checked_in"
    assert body["checked_in_at"] == "2026-11-26T16:10:00Z"
    assert body["overdue"] is False

    repeated = await client.post(
        f"/api/v1/guests/{visit_id}/check-in", headers=_auth(token)
    )
    assert repeated.status_code == 409
    assert repeated.json()["code"] == "guest_check_in_blocked"


async def test_check_in_is_blocked_outside_the_window(client, app, frozen_now) -> None:
    await _register(client, RESIDENT, "سارا محمدی")
    host_id = await _id_of(app, RESIDENT)
    token = await _manager(client, app)
    visit_id = await _visit(app, host_id, guest_name="مریم احمدی")

    frozen_now["now"] = BASE - timedelta(minutes=5)
    early = await client.post(f"/api/v1/guests/{visit_id}/check-in", headers=_auth(token))

    frozen_now["now"] = WINDOW_END + timedelta(minutes=5)
    late = await client.post(f"/api/v1/guests/{visit_id}/check-in", headers=_auth(token))

    assert early.status_code == 409
    assert early.json()["code"] == "guest_check_in_blocked"
    assert late.status_code == 409
    assert late.json()["code"] == "guest_check_in_blocked"


async def test_check_out_records_the_exit_and_flags_a_late_one(client, app, frozen_now) -> None:
    await _register(client, RESIDENT, "سارا محمدی")
    host_id = await _id_of(app, RESIDENT)
    token = await _manager(client, app)
    visit_id = await _visit(
        app,
        host_id,
        guest_name="مریم احمدی",
        status="checked_in",
        checked_in_at=BASE + timedelta(minutes=10),
    )

    frozen_now["now"] = WINDOW_END + timedelta(minutes=30)
    response = await client.post(
        f"/api/v1/guests/{visit_id}/check-out", headers=_auth(token)
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "checked_out"
    assert body["checked_out_at"] == "2026-11-26T18:30:00Z"
    assert body["overdue"] is True


async def test_check_out_requires_a_guest_inside(client, app, frozen_now) -> None:
    await _register(client, RESIDENT, "سارا محمدی")
    host_id = await _id_of(app, RESIDENT)
    token = await _manager(client, app)
    visit_id = await _visit(app, host_id, guest_name="مریم احمدی")

    response = await client.post(
        f"/api/v1/guests/{visit_id}/check-out", headers=_auth(token)
    )

    assert response.status_code == 409
    assert response.json()["code"] == "guest_check_out_blocked"


async def test_detail_of_an_unknown_visit_is_404(client, app, frozen_now) -> None:
    token = await _manager(client, app)
    response = await client.get(f"/api/v1/guests/{uuid4()}", headers=_auth(token))
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


async def test_a_resident_cannot_use_the_desk(client, app, frozen_now) -> None:
    resident_token = await _register(client, RESIDENT, "سارا محمدی")
    host_id = await _id_of(app, RESIDENT)
    visit_id = await _visit(app, host_id, guest_name="مریم احمدی")

    listing = await client.get("/api/v1/guests", headers=_auth(resident_token))
    detail = await client.get(f"/api/v1/guests/{visit_id}", headers=_auth(resident_token))
    register = await client.post(
        "/api/v1/guests", headers=_auth(resident_token), json=_payload()
    )
    check_in = await client.post(
        f"/api/v1/guests/{visit_id}/check-in", headers=_auth(resident_token)
    )
    check_out = await client.post(
        f"/api/v1/guests/{visit_id}/check-out", headers=_auth(resident_token)
    )

    assert listing.status_code == 403
    assert detail.status_code == 403
    assert register.status_code == 403
    assert check_in.status_code == 403
    assert check_out.status_code == 403
