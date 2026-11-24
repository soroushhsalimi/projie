"""Integration tests for ticket persistence (SPEC-0004 FR-1, FR-2)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sara_api.modules.tickets.models import Ticket, TicketMessage
from sara_api.modules.tickets.repository import TicketRepository
from sara_api.modules.users.models import User

BASE = datetime(2026, 11, 20, 8, 0, tzinfo=UTC)


async def _user(session, email: str, role: str = "user") -> User:  # type: ignore[no-untyped-def]
    user = User(
        email=email,
        password_hash="x",
        full_name=email.split("@", 1)[0],
        role=role,
        status="active",
    )
    session.add(user)
    await session.flush()
    return user


async def test_list_orders_newest_first_and_filters_by_status(app) -> None:
    async with app.state.sessionmaker() as session:
        reporter = await _user(session, "resident@example.com")
        repository = TicketRepository(session)
        await repository.add(
            Ticket(
                reporter_id=reporter.id,
                subject="older open",
                description="d",
                category="general",
                status="open",
                created_at=BASE,
                updated_at=BASE,
            )
        )
        await repository.add(
            Ticket(
                reporter_id=reporter.id,
                subject="newer open",
                description="d",
                category="plumbing",
                status="open",
                created_at=BASE + timedelta(hours=1),
                updated_at=BASE + timedelta(hours=1),
            )
        )
        await repository.add(
            Ticket(
                reporter_id=reporter.id,
                subject="resolved one",
                description="d",
                category="general",
                status="resolved",
                created_at=BASE + timedelta(hours=2),
                updated_at=BASE + timedelta(hours=2),
            )
        )
        await session.flush()

        rows = await repository.list_with_reporter(status="open", limit=10, offset=0)
        assert [ticket.subject for ticket, _ in rows] == ["newer open", "older open"]
        assert rows[0][1] == "resident"
        assert await repository.count(status="open") == 2
        assert await repository.count(status=None) == 3


async def test_messages_keep_chronological_order_with_author_roles(app) -> None:
    async with app.state.sessionmaker() as session:
        reporter = await _user(session, "resident@example.com")
        manager = await _user(session, "manager@example.com", role="manager")
        repository = TicketRepository(session)
        ticket = await repository.add(
            Ticket(
                reporter_id=reporter.id,
                subject="broken heater",
                description="d",
                category="heating",
                status="open",
            )
        )
        await repository.add_message(
            TicketMessage(
                ticket_id=ticket.id,
                author_id=manager.id,
                body="second",
                created_at=BASE + timedelta(minutes=10),
                updated_at=BASE + timedelta(minutes=10),
            )
        )
        await repository.add_message(
            TicketMessage(
                ticket_id=ticket.id,
                author_id=reporter.id,
                body="first",
                created_at=BASE,
                updated_at=BASE,
            )
        )
        await session.flush()

        found = await repository.get_with_reporter(ticket.id)
        assert found is not None
        assert found[1] == "resident"
        rows = await repository.list_messages(ticket.id)
        assert [message.body for message, _, _ in rows] == ["first", "second"]
        assert [(name, role) for _, name, role in rows] == [
            ("resident", "user"),
            ("manager", "manager"),
        ]
