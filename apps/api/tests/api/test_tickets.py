"""API contract tests for maintenance tickets (SPEC-0004 FR-1…FR-6)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select

from helpers import registration_body
from sara_api.modules.tickets.models import Ticket, TicketMessage
from sara_api.modules.users.models import User

PASSWORD = "CorrectHorseBatteryStaple"
BASE = datetime(2026, 11, 20, 9, 0, tzinfo=UTC)
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


async def _ticket(  # type: ignore[no-untyped-def]
    app,
    reporter_id: UUID,
    *,
    subject: str,
    status: str = "open",
    created_at: datetime = BASE,
) -> UUID:
    async with app.state.sessionmaker() as session:
        ticket = Ticket(
            reporter_id=reporter_id,
            subject=subject,
            description="توضیح مشکل",
            category="general",
            status=status,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add(ticket)
        await session.commit()
        return ticket.id


async def _message(app, ticket_id: UUID, author_id: UUID, body: str, at: datetime) -> None:  # type: ignore[no-untyped-def]
    async with app.state.sessionmaker() as session:
        session.add(
            TicketMessage(
                ticket_id=ticket_id,
                author_id=author_id,
                body=body,
                created_at=at,
                updated_at=at,
            )
        )
        await session.commit()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_list_requires_auth(client) -> None:
    response = await client.get("/api/v1/tickets")
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_token"


async def test_list_rejects_a_resident(client, app) -> None:
    await _register(client, RESIDENT, "سارا محمدی")
    token = await _register(client, "other@example.com", "کاربر دیگر")

    response = await client.get("/api/v1/tickets", headers=_auth(token))

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


async def test_list_filters_by_status_and_paginates(client, app) -> None:
    resident_token = await _register(client, RESIDENT, "سارا محمدی")
    assert resident_token
    reporter_id = await _id_of(app, RESIDENT)
    token = await _manager(client, app)

    await _ticket(app, reporter_id, subject="older open", created_at=BASE)
    await _ticket(app, reporter_id, subject="newer open", created_at=BASE + timedelta(hours=1))
    await _ticket(
        app,
        reporter_id,
        subject="resolved one",
        status="resolved",
        created_at=BASE + timedelta(hours=2),
    )

    response = await client.get("/api/v1/tickets?status=open", headers=_auth(token))

    assert response.status_code == 200
    body = response.json()
    assert [item["subject"] for item in body["items"]] == ["newer open", "older open"]
    assert body["meta"] == {"page": 1, "per_page": 20, "total": 2}
    assert body["items"][0]["reporter_name"] == "سارا محمدی"

    second_page = await client.get(
        "/api/v1/tickets?status=open&page=2&per_page=1", headers=_auth(token)
    )
    assert [item["subject"] for item in second_page.json()["items"]] == ["older open"]


async def test_list_rejects_unknown_status_filter(client, app) -> None:
    token = await _manager(client, app)
    response = await client.get("/api/v1/tickets?status=archived", headers=_auth(token))
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


async def test_list_rejects_oversized_page_size(client, app) -> None:
    token = await _manager(client, app)
    response = await client.get("/api/v1/tickets?per_page=500", headers=_auth(token))
    assert response.status_code == 422


async def test_detail_returns_the_thread(client, app) -> None:
    await _register(client, RESIDENT, "سارا محمدی")
    reporter_id = await _id_of(app, RESIDENT)
    token = await _manager(client, app)
    manager_id = await _id_of(app, MANAGER)
    ticket_id = await _ticket(app, reporter_id, subject="خرابی بخاری")
    await _message(app, ticket_id, manager_id, "پاسخ مدیر", BASE + timedelta(minutes=5))
    await _message(app, ticket_id, reporter_id, "پیام ساکن", BASE)

    response = await client.get(f"/api/v1/tickets/{ticket_id}", headers=_auth(token))

    assert response.status_code == 200
    body = response.json()
    assert body["subject"] == "خرابی بخاری"
    assert body["status"] == "open"
    assert body["reporter_name"] == "سارا محمدی"
    assert [message["body"] for message in body["messages"]] == ["پیام ساکن", "پاسخ مدیر"]
    assert body["messages"][1]["author_role"] == "manager"


async def test_detail_of_unknown_ticket_is_404(client, app) -> None:
    token = await _manager(client, app)
    response = await client.get(f"/api/v1/tickets/{uuid4()}", headers=_auth(token))
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


async def test_reply_appends_a_manager_message(client, app) -> None:
    await _register(client, RESIDENT, "سارا محمدی")
    reporter_id = await _id_of(app, RESIDENT)
    token = await _manager(client, app)
    ticket_id = await _ticket(app, reporter_id, subject="نشتی آب")

    response = await client.post(
        f"/api/v1/tickets/{ticket_id}/messages",
        headers=_auth(token),
        json={"body": "لوله‌کش فردا ساعت ۱۰ می‌آید."},
    )

    assert response.status_code == 201
    messages = response.json()["messages"]
    assert messages[-1]["body"] == "لوله‌کش فردا ساعت ۱۰ می‌آید."
    assert messages[-1]["author_name"] == "رضا کریمی"
    assert messages[-1]["author_role"] == "manager"


async def test_reply_rejects_a_blank_body(client, app) -> None:
    await _register(client, RESIDENT, "سارا محمدی")
    reporter_id = await _id_of(app, RESIDENT)
    token = await _manager(client, app)
    ticket_id = await _ticket(app, reporter_id, subject="نشتی آب")

    response = await client.post(
        f"/api/v1/tickets/{ticket_id}/messages",
        headers=_auth(token),
        json={"body": "   "},
    )

    assert response.status_code == 422


async def test_status_changes_follow_the_state_machine(client, app) -> None:
    await _register(client, RESIDENT, "سارا محمدی")
    reporter_id = await _id_of(app, RESIDENT)
    token = await _manager(client, app)
    ticket_id = await _ticket(app, reporter_id, subject="تخت شکسته")

    under_review = await client.patch(
        f"/api/v1/tickets/{ticket_id}/status",
        headers=_auth(token),
        json={"status": "under_review"},
    )
    assert under_review.status_code == 200
    assert under_review.json()["status"] == "under_review"

    resolved = await client.patch(
        f"/api/v1/tickets/{ticket_id}/status",
        headers=_auth(token),
        json={"status": "resolved"},
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"

    repeated = await client.patch(
        f"/api/v1/tickets/{ticket_id}/status",
        headers=_auth(token),
        json={"status": "resolved"},
    )
    assert repeated.status_code == 409
    assert repeated.json()["code"] == "ticket_transition_not_allowed"


async def test_status_update_rejects_an_unknown_state(client, app) -> None:
    await _register(client, RESIDENT, "سارا محمدی")
    reporter_id = await _id_of(app, RESIDENT)
    token = await _manager(client, app)
    ticket_id = await _ticket(app, reporter_id, subject="تخت شکسته")

    response = await client.patch(
        f"/api/v1/tickets/{ticket_id}/status",
        headers=_auth(token),
        json={"status": "archived"},
    )

    assert response.status_code == 422


async def test_resident_cannot_reply_or_change_status(client, app) -> None:
    resident_token = await _register(client, RESIDENT, "سارا محمدی")
    reporter_id = await _id_of(app, RESIDENT)
    ticket_id = await _ticket(app, reporter_id, subject="تخت شکسته")

    reply = await client.post(
        f"/api/v1/tickets/{ticket_id}/messages",
        headers=_auth(resident_token),
        json={"body": "سلام"},
    )
    status_change = await client.patch(
        f"/api/v1/tickets/{ticket_id}/status",
        headers=_auth(resident_token),
        json={"status": "resolved"},
    )
    detail = await client.get(f"/api/v1/tickets/{ticket_id}", headers=_auth(resident_token))

    assert reply.status_code == 403
    assert status_change.status_code == 403
    assert detail.status_code == 403
