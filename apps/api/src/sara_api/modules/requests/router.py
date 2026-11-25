"""Accommodation-request HTTP endpoints (residents only)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from sara_api.api.deps import get_request_service, require_roles
from sara_api.domain.accounts import Role
from sara_api.domain.requests import RequestStatus, RoomType
from sara_api.modules.requests.models import AccommodationRequest
from sara_api.modules.requests.schemas import (
    AccommodationRequestRead,
    PageMeta,
    RequestCreate,
    RequestPageRead,
)
from sara_api.modules.requests.service import RequestPage, RequestService
from sara_api.modules.users.models import User

router = APIRouter(prefix="/requests", tags=["requests"])


def _read(request: AccommodationRequest) -> AccommodationRequestRead:
    return AccommodationRequestRead(
        id=request.id,
        dormitory_name=request.dormitory_name,
        room_type=RoomType(request.room_type),
        desired_move_in=request.desired_move_in,
        duration_months=request.duration_months,
        note=request.note,
        status=RequestStatus(request.status),
        created_at=request.created_at,
        updated_at=request.updated_at,
    )


def _page(page: RequestPage) -> RequestPageRead:
    return RequestPageRead(
        items=[_read(request) for request in page.items],
        meta=PageMeta(page=page.page, per_page=page.per_page, total=page.total),
    )


@router.get(
    "",
    response_model=RequestPageRead,
    summary="List my accommodation requests",
    description="Only the caller's requests, newest first.",
)
async def list_requests(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    service: RequestService = Depends(get_request_service),
    resident: User = Depends(require_roles(Role.USER)),
) -> RequestPageRead:
    return _page(await service.list_requests(resident.id, page=page, per_page=per_page))


@router.post(
    "",
    response_model=AccommodationRequestRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit an accommodation request",
    description="A resident may hold at most one active (submitted) request.",
)
async def create_request(
    payload: RequestCreate,
    service: RequestService = Depends(get_request_service),
    resident: User = Depends(require_roles(Role.USER)),
) -> AccommodationRequestRead:
    request = await service.submit(
        resident.id,
        dormitory_name=payload.dormitory_name,
        room_type=payload.room_type,
        desired_move_in=payload.desired_move_in,
        duration_months=payload.duration_months,
        note=payload.note,
    )
    return _read(request)


@router.post(
    "/{request_id}/withdraw",
    response_model=AccommodationRequestRead,
    summary="Withdraw an accommodation request",
    description="Only a request that is still submitted can be withdrawn.",
)
async def withdraw_request(
    request_id: UUID,
    service: RequestService = Depends(get_request_service),
    resident: User = Depends(require_roles(Role.USER)),
) -> AccommodationRequestRead:
    return _read(await service.withdraw(resident.id, request_id))
