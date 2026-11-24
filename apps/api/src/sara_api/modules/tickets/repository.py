"""Ticket persistence. SQL lives here and nowhere above it (AGENTS.md §5)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from sara_api.modules.tickets.models import Ticket, TicketMessage
from sara_api.modules.users.models import User


class TicketRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_with_reporter(
        self,
        *,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[tuple[Ticket, str]]:
        statement = (
            select(Ticket, User.full_name)
            .join(User, User.id == Ticket.reporter_id)
            .order_by(Ticket.created_at.desc(), Ticket.id.desc())
            .limit(limit)
            .offset(offset)
        )
        if status is not None:
            statement = statement.where(Ticket.status == status)
        result = await self._session.execute(statement)
        return [(ticket, name) for ticket, name in result.all()]

    async def count(self, *, status: str | None) -> int:
        statement = select(func.count()).select_from(Ticket)
        if status is not None:
            statement = statement.where(Ticket.status == status)
        result = await self._session.execute(statement)
        return int(result.scalar_one())

    async def get_with_reporter(self, ticket_id: UUID) -> tuple[Ticket, str] | None:
        result = await self._session.execute(
            select(Ticket, User.full_name)
            .join(User, User.id == Ticket.reporter_id)
            .where(Ticket.id == ticket_id)
        )
        row = result.first()
        return (row[0], row[1]) if row is not None else None

    async def list_messages(self, ticket_id: UUID) -> list[tuple[TicketMessage, str, str]]:
        """Return ``(message, author_name, author_role)`` ordered oldest first."""
        result = await self._session.execute(
            select(TicketMessage, User.full_name, User.role)
            .join(User, User.id == TicketMessage.author_id)
            .where(TicketMessage.ticket_id == ticket_id)
            .order_by(TicketMessage.created_at.asc(), TicketMessage.id.asc())
        )
        return [(message, name, role) for message, name, role in result.all()]

    async def add(self, ticket: Ticket) -> Ticket:
        self._session.add(ticket)
        await self._session.flush()
        return ticket

    async def add_message(self, message: TicketMessage) -> TicketMessage:
        self._session.add(message)
        await self._session.flush()
        return message

    async def save(self, ticket: Ticket) -> Ticket:
        await self._session.flush()
        return ticket
