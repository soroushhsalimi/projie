"""Guest-visit HTTP endpoints (manager and admin / front desk only)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from sara_api.api.deps import get_guest_service, require_roles
from sara_api.domain.accounts import Role
from sara_api.domain.guests import GuestStatus
from sara_api.modules.guests.schemas import (
    GuestVisitCreate,
    GuestVisitPageRead,
    GuestVisitRead,
    PageMeta,
)
from sara_api.modules.guests.service import GuestService, GuestVisitItem, GuestVisitPage

router = APIRouter(
    prefix="/guests",
    tags=["guests"],
    dependencies=[Depends(require_roles(Role.MANAGER, Role.ADMIN))],
)


def _read(item: GuestVisitItem) -> GuestVisitRead:
    visit = item.visit
    return GuestVisitRead(
        id=visit.id,
        guest_name=visit.guest_name,
        host_name=item.host_name,
        purpose=visit.purpose,
        status=GuestStatus(visit.status),
        allowed_from=visit.allowed_from,
        allowed_until=visit.allowed_until,
        checked_in_at=visit.checked_in_at,
        checked_out_at=visit.checked_out_at,
        overdue=item.overdue,
        created_at=visit.created_at,
        updated_at=visit.updated_at,
    )


def _page(page: GuestVisitPage) -> GuestVisitPageRead:
    return GuestVisitPageRead(
        items=[_read(item) for item in page.items],
        meta=PageMeta(page=page.page, per_page=page.per_page, total=page.total),
    )


@router.get(
    "",
    response_model=GuestVisitPageRead,
    summary="List guest visits",
    description="Front-desk queue, newest first, optionally filtered by status.",
)
async def list_guest_visits(
    status_filter: GuestStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    service: GuestService = Depends(get_guest_service),
) -> GuestVisitPageRead:
    return _page(
        await service.list_visits(status=status_filter, page=page, per_page=per_page)
    )


@router.post(
    "",
    response_model=GuestVisitRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a guest visit",
    description="Records the guest, the hosting resident and the allowed window.",
)
async def register_guest_visit(
    payload: GuestVisitCreate,
    service: GuestService = Depends(get_guest_service),
) -> GuestVisitRead:
    return _read(
        await service.register_visit(
            guest_name=payload.guest_name,
            host_email=str(payload.host_email),
            purpose=payload.purpose,
            allowed_from=payload.allowed_from,
            allowed_until=payload.allowed_until,
        )
    )


@router.get(
    "/{visit_id}",
    response_model=GuestVisitRead,
    summary="Guest visit detail",
)
async def get_guest_visit(
    visit_id: UUID,
    service: GuestService = Depends(get_guest_service),
) -> GuestVisitRead:
    return _read(await service.get_visit(visit_id))


@router.post(
    "/{visit_id}/check-in",
    response_model=GuestVisitRead,
    summary="Check a guest in",
    description="Legal only for an expected visit inside its allowed window.",
)
async def check_guest_in(
    visit_id: UUID,
    service: GuestService = Depends(get_guest_service),
) -> GuestVisitRead:
    return _read(await service.check_in(visit_id))


@router.post(
    "/{visit_id}/check-out",
    response_model=GuestVisitRead,
    summary="Check a guest out",
    description="Legal only for a checked-in visit; a late exit is flagged as overdue.",
)
async def check_guest_out(
    visit_id: UUID,
    service: GuestService = Depends(get_guest_service),
) -> GuestVisitRead:
    return _read(await service.check_out(visit_id))
