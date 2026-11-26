"""API contract tests for complaints management (SPEC-0007 FR-1…FR-6)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select

from helpers import registration_body
from sara_api.modules.complaints.models import Complaint, ComplaintResponse
from sara_api.modules.users.models import User

PASSWORD = "CorrectHorseBatteryStaple"
BASE = datetime(2026, 11, 22, 9, 0, tzinfo=UTC)
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


async def _complaint(  # type: ignore[no-untyped-def]
    app,
    resident_id: UUID,
    *,
    subject: str,
    status: str = "submitted",
    created_at: datetime = BASE,
) -> UUID:
    async with app.state.sessionmaker() as session:
        complaint = Complaint(
            resident_id=resident_id,
            subject=subject,
            description="شرح شکایت",
            category="noise",
            status=status,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add(complaint)
        await session.commit()
        return complaint.id


async def _response(app, complaint_id: UUID, responder_id: UUID, body: str) -> None:  # type: ignore[no-untyped-def]
    async with app.state.sessionmaker() as session:
        session.add(
            ComplaintResponse(
                complaint_id=complaint_id,
                responder_id=responder_id,
                body=body,
            )
        )
        await session.commit()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_list_requires_auth(client) -> None:
    response = await client.get("/api/v1/complaints")
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_token"


async def test_list_rejects_a_resident(client) -> None:
    token = await _register(client, RESIDENT, "سارا محمدی")

    response = await client.get("/api/v1/complaints", headers=_auth(token))

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


async def test_list_filters_by_status_and_paginates(client, app) -> None:
    await _register(client, RESIDENT, "سارا محمدی")
    resident_id = await _id_of(app, RESIDENT)
    token = await _manager(client, app)

    await _complaint(app, resident_id, subject="older submitted", created_at=BASE)
    await _complaint(
        app, resident_id, subject="newer submitted", created_at=BASE + timedelta(hours=1)
    )
    await _complaint(
        app,
        resident_id,
        subject="in review one",
        status="in_review",
        created_at=BASE + timedelta(hours=2),
    )

    response = await client.get("/api/v1/complaints?status=submitted", headers=_auth(token))

    assert response.status_code == 200
    body = response.json()
    assert [item["subject"] for item in body["items"]] == [
        "newer submitted",
        "older submitted",
    ]
    assert body["meta"] == {"page": 1, "per_page": 20, "total": 2}
    assert body["items"][0]["resident_name"] == "سارا محمدی"

    second_page = await client.get(
        "/api/v1/complaints?status=submitted&page=2&per_page=1", headers=_auth(token)
    )
    assert [item["subject"] for item in second_page.json()["items"]] == ["older submitted"]


async def test_list_rejects_unknown_status_filter(client, app) -> None:
    token = await _manager(client, app)
    response = await client.get("/api/v1/complaints?status=closed", headers=_auth(token))
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


async def test_detail_returns_the_initial_response(client, app) -> None:
    await _register(client, RESIDENT, "سارا محمدی")
    resident_id = await _id_of(app, RESIDENT)
    token = await _manager(client, app)
    manager_id = await _id_of(app, MANAGER)
    complaint_id = await _complaint(app, resident_id, subject="سر و صدای شبانه")
    await _response(app, complaint_id, manager_id, "تذکر داده شد.")

    response = await client.get(f"/api/v1/complaints/{complaint_id}", headers=_auth(token))

    assert response.status_code == 200
    body = response.json()
    assert body["subject"] == "سر و صدای شبانه"
    assert body["resident_name"] == "سارا محمدی"
    assert body["response"]["body"] == "تذکر داده شد."
    assert body["response"]["responder_name"] == "رضا کریمی"


async def test_detail_without_a_response_is_empty(client, app) -> None:
    await _register(client, RESIDENT, "سارا محمدی")
    resident_id = await _id_of(app, RESIDENT)
    token = await _manager(client, app)
    complaint_id = await _complaint(app, resident_id, subject="نظافت راه‌پله")

    response = await client.get(f"/api/v1/complaints/{complaint_id}", headers=_auth(token))

    assert response.status_code == 200
    assert response.json()["response"] is None


async def test_detail_of_unknown_complaint_is_404(client, app) -> None:
    token = await _manager(client, app)
    response = await client.get(f"/api/v1/complaints/{uuid4()}", headers=_auth(token))
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


async def test_start_review_moves_a_submitted_complaint_once(client, app) -> None:
    await _register(client, RESIDENT, "سارا محمدی")
    resident_id = await _id_of(app, RESIDENT)
    token = await _manager(client, app)
    complaint_id = await _complaint(app, resident_id, subject="خرابی آسانسور")

    first = await client.post(
        f"/api/v1/complaints/{complaint_id}/status",
        headers=_auth(token),
        json={"status": "in_review"},
    )
    assert first.status_code == 200
    assert first.json()["status"] == "in_review"

    repeated = await client.post(
        f"/api/v1/complaints/{complaint_id}/status",
        headers=_auth(token),
        json={"status": "in_review"},
    )
    assert repeated.status_code == 409
    assert repeated.json()["code"] == "complaint_transition_not_allowed"


async def test_status_update_rejects_an_unknown_state(client, app) -> None:
    await _register(client, RESIDENT, "سارا محمدی")
    resident_id = await _id_of(app, RESIDENT)
    token = await _manager(client, app)
    complaint_id = await _complaint(app, resident_id, subject="خرابی آسانسور")

    response = await client.post(
        f"/api/v1/complaints/{complaint_id}/status",
        headers=_auth(token),
        json={"status": "answered"},
    )

    assert response.status_code == 422


async def test_response_is_recorded_once_and_answers_the_complaint(client, app) -> None:
    await _register(client, RESIDENT, "سارا محمدی")
    resident_id = await _id_of(app, RESIDENT)
    token = await _manager(client, app)
    complaint_id = await _complaint(app, resident_id, subject="سر و صدای شبانه")

    created = await client.post(
        f"/api/v1/complaints/{complaint_id}/response",
        headers=_auth(token),
        json={"body": "با ساکنان طبقه سوم صحبت شد."},
    )

    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "answered"
    assert body["response"]["body"] == "با ساکنان طبقه سوم صحبت شد."
    assert body["response"]["responder_name"] == "رضا کریمی"

    repeated = await client.post(
        f"/api/v1/complaints/{complaint_id}/response",
        headers=_auth(token),
        json={"body": "پاسخ دوم"},
    )
    assert repeated.status_code == 409
    assert repeated.json()["code"] == "complaint_already_answered"


async def test_response_rejects_a_blank_body(client, app) -> None:
    await _register(client, RESIDENT, "سارا محمدی")
    resident_id = await _id_of(app, RESIDENT)
    token = await _manager(client, app)
    complaint_id = await _complaint(app, resident_id, subject="سر و صدای شبانه")

    response = await client.post(
        f"/api/v1/complaints/{complaint_id}/response",
        headers=_auth(token),
        json={"body": "   "},
    )

    assert response.status_code == 422


async def test_resident_cannot_read_or_answer_a_complaint(client, app) -> None:
    resident_token = await _register(client, RESIDENT, "سارا محمدی")
    resident_id = await _id_of(app, RESIDENT)
    complaint_id = await _complaint(app, resident_id, subject="سر و صدای شبانه")

    detail = await client.get(
        f"/api/v1/complaints/{complaint_id}", headers=_auth(resident_token)
    )
    answer = await client.post(
        f"/api/v1/complaints/{complaint_id}/response",
        headers=_auth(resident_token),
        json={"body": "پاسخ ساکن"},
    )
    review = await client.post(
        f"/api/v1/complaints/{complaint_id}/status",
        headers=_auth(resident_token),
        json={"status": "in_review"},
    )

    assert detail.status_code == 403
    assert answer.status_code == 403
    assert review.status_code == 403
