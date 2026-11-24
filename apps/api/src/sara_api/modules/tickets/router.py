"""Maintenance-ticket HTTP endpoints (manager and admin only)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from sara_api.api.deps import get_ticket_service, require_roles
from sara_api.domain.accounts import Role
from sara_api.domain.tickets import TicketCategory, TicketStatus
from sara_api.modules.tickets.schemas import (
    PageMeta,
    TicketDetailRead,
    TicketMessageRead,
    TicketPageRead,
    TicketReplyRequest,
    TicketStatusUpdate,
    TicketSummaryRead,
)
from sara_api.modules.tickets.service import TicketDetail, TicketListItem, TicketPage, TicketService
from sara_api.modules.users.models import User

router = APIRouter(
    prefix="/tickets",
    tags=["tickets"],
    dependencies=[Depends(require_roles(Role.MANAGER, Role.ADMIN))],
)


def _summary(item: TicketListItem) -> TicketSummaryRead:
    ticket = item.ticket
    return TicketSummaryRead(
        id=ticket.id,
        subject=ticket.subject,
        category=TicketCategory(ticket.category),
        status=TicketStatus(ticket.status),
        reporter_name=item.reporter_name,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )


def _detail(detail: TicketDetail) -> TicketDetailRead:
    ticket = detail.ticket
    return TicketDetailRead(
        id=ticket.id,
        subject=ticket.subject,
        category=TicketCategory(ticket.category),
        status=TicketStatus(ticket.status),
        reporter_name=detail.reporter_name,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        description=ticket.description,
        messages=[
            TicketMessageRead(
                id=record.message.id,
                author_name=record.author_name,
                author_role=Role(record.author_role),
                body=record.message.body,
                created_at=record.message.created_at,
            )
            for record in detail.messages
        ],
    )


def _page(page: TicketPage) -> TicketPageRead:
    return TicketPageRead(
        items=[_summary(item) for item in page.items],
        meta=PageMeta(page=page.page, per_page=page.per_page, total=page.total),
    )


@router.get(
    "",
    response_model=TicketPageRead,
    summary="List maintenance tickets",
    description="Manager queue, newest first, optionally filtered by status.",
)
async def list_tickets(
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    service: TicketService = Depends(get_ticket_service),
) -> TicketPageRead:
    result = await service.list_tickets(status=status_filter, page=page, per_page=per_page)
    return _page(result)


@router.get(
    "/{ticket_id}",
    response_model=TicketDetailRead,
    summary="Ticket detail with its message thread",
)
async def get_ticket(
    ticket_id: UUID,
    service: TicketService = Depends(get_ticket_service),
) -> TicketDetailRead:
    return _detail(await service.get_ticket(ticket_id))


@router.post(
    "/{ticket_id}/messages",
    response_model=TicketDetailRead,
    status_code=status.HTTP_201_CREATED,
    summary="Reply to a ticket",
    description="Appends a manager reply and returns the refreshed thread.",
)
async def reply_to_ticket(
    ticket_id: UUID,
    payload: TicketReplyRequest,
    service: TicketService = Depends(get_ticket_service),
    manager: User = Depends(require_roles(Role.MANAGER, Role.ADMIN)),
) -> TicketDetailRead:
    return _detail(await service.reply(ticket_id, author_id=manager.id, body=payload.body))


@router.patch(
    "/{ticket_id}/status",
    response_model=TicketDetailRead,
    summary="Change a ticket status",
    description="Legal moves: open → under_review, open → resolved, under_review → resolved.",
)
async def change_ticket_status(
    ticket_id: UUID,
    payload: TicketStatusUpdate,
    service: TicketService = Depends(get_ticket_service),
) -> TicketDetailRead:
    return _detail(await service.change_status(ticket_id, target=TicketStatus(payload.status)))
