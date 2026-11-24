"""Maintenance-ticket use cases.

The service owns the unit of work (it never commits) and contains no FastAPI imports. Role
enforcement happens in the transport layer; this layer owns existence and the status machine.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from sara_api.core.errors import NotFound, TicketTransitionBlocked
from sara_api.domain.tickets import TicketStatus, TicketTransitionNotAllowed, ensure_transition
from sara_api.modules.tickets.models import Ticket, TicketMessage
from sara_api.modules.tickets.repository import TicketRepository

logger = logging.getLogger("sara.tickets")


@dataclass(frozen=True, slots=True)
class TicketListItem:
    ticket: Ticket
    reporter_name: str


@dataclass(frozen=True, slots=True)
class MessageRecord:
    message: TicketMessage
    author_name: str
    author_role: str


@dataclass(frozen=True, slots=True)
class TicketDetail:
    ticket: Ticket
    reporter_name: str
    messages: list[MessageRecord]


@dataclass(frozen=True, slots=True)
class TicketPage:
    items: list[TicketListItem]
    total: int
    page: int
    per_page: int


class TicketService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = TicketRepository(session)

    async def list_tickets(
        self,
        *,
        status: TicketStatus | None,
        page: int,
        per_page: int,
    ) -> TicketPage:
        status_value = status.value if status is not None else None
        total = await self._repo.count(status=status_value)
        rows = await self._repo.list_with_reporter(
            status=status_value,
            limit=per_page,
            offset=(page - 1) * per_page,
        )
        return TicketPage(
            items=[TicketListItem(ticket=ticket, reporter_name=name) for ticket, name in rows],
            total=total,
            page=page,
            per_page=per_page,
        )

    async def get_ticket(self, ticket_id: UUID) -> TicketDetail:
        ticket, reporter_name = await self._require(ticket_id)
        return await self._detail(ticket, reporter_name)

    async def reply(self, ticket_id: UUID, *, author_id: UUID, body: str) -> TicketDetail:
        ticket, reporter_name = await self._require(ticket_id)
        await self._repo.add_message(
            TicketMessage(ticket_id=ticket.id, author_id=author_id, body=body.strip())
        )
        logger.info("ticket.reply.added", extra={"ticket_id": str(ticket.id)})
        return await self._detail(ticket, reporter_name)

    async def change_status(self, ticket_id: UUID, *, target: TicketStatus) -> TicketDetail:
        ticket, reporter_name = await self._require(ticket_id)
        current = TicketStatus(ticket.status)
        try:
            ensure_transition(current, target)
        except TicketTransitionNotAllowed as exc:
            raise TicketTransitionBlocked(
                f"A ticket in status '{current}' cannot move to '{target}'."
            ) from exc
        ticket.status = target.value
        await self._repo.save(ticket)
        logger.info(
            "ticket.status.changed",
            extra={"ticket_id": str(ticket.id), "status": target.value},
        )
        return await self._detail(ticket, reporter_name)

    async def _require(self, ticket_id: UUID) -> tuple[Ticket, str]:
        row = await self._repo.get_with_reporter(ticket_id)
        if row is None:
            raise NotFound("Ticket not found.")
        return row

    async def _detail(self, ticket: Ticket, reporter_name: str) -> TicketDetail:
        rows = await self._repo.list_messages(ticket.id)
        return TicketDetail(
            ticket=ticket,
            reporter_name=reporter_name,
            messages=[
                MessageRecord(message=message, author_name=name, author_role=role)
                for message, name, role in rows
            ],
        )
