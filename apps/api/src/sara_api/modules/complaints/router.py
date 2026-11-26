"""Complaint HTTP endpoints (manager and admin only)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from sara_api.api.deps import get_complaint_service, require_roles
from sara_api.domain.accounts import Role
from sara_api.domain.complaints import ComplaintCategory, ComplaintStatus
from sara_api.modules.complaints.schemas import (
    ComplaintDetailRead,
    ComplaintPageRead,
    ComplaintResponseRead,
    ComplaintResponseRequest,
    ComplaintStatusUpdate,
    ComplaintSummaryRead,
    PageMeta,
)
from sara_api.modules.complaints.service import (
    ComplaintDetail,
    ComplaintListItem,
    ComplaintPage,
    ComplaintService,
)
from sara_api.modules.users.models import User

router = APIRouter(
    prefix="/complaints",
    tags=["complaints"],
    dependencies=[Depends(require_roles(Role.MANAGER, Role.ADMIN))],
)


def _summary(item: ComplaintListItem) -> ComplaintSummaryRead:
    complaint = item.complaint
    return ComplaintSummaryRead(
        id=complaint.id,
        subject=complaint.subject,
        category=ComplaintCategory(complaint.category),
        status=ComplaintStatus(complaint.status),
        resident_name=item.resident_name,
        created_at=complaint.created_at,
        updated_at=complaint.updated_at,
    )


def _detail(detail: ComplaintDetail) -> ComplaintDetailRead:
    complaint = detail.complaint
    response = detail.response
    return ComplaintDetailRead(
        id=complaint.id,
        subject=complaint.subject,
        category=ComplaintCategory(complaint.category),
        status=ComplaintStatus(complaint.status),
        resident_name=detail.resident_name,
        created_at=complaint.created_at,
        updated_at=complaint.updated_at,
        description=complaint.description,
        response=(
            ComplaintResponseRead(
                id=response.response.id,
                body=response.response.body,
                responder_name=response.responder_name,
                created_at=response.response.created_at,
            )
            if response is not None
            else None
        ),
    )


def _page(page: ComplaintPage) -> ComplaintPageRead:
    return ComplaintPageRead(
        items=[_summary(item) for item in page.items],
        meta=PageMeta(page=page.page, per_page=page.per_page, total=page.total),
    )


@router.get(
    "",
    response_model=ComplaintPageRead,
    summary="List resident complaints",
    description="Manager queue, newest first, optionally filtered by status.",
)
async def list_complaints(
    status_filter: ComplaintStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    service: ComplaintService = Depends(get_complaint_service),
) -> ComplaintPageRead:
    result = await service.list_complaints(
        status=status_filter, page=page, per_page=per_page
    )
    return _page(result)


@router.get(
    "/{complaint_id}",
    response_model=ComplaintDetailRead,
    summary="Complaint detail with its initial response",
)
async def get_complaint(
    complaint_id: UUID,
    service: ComplaintService = Depends(get_complaint_service),
) -> ComplaintDetailRead:
    return _detail(await service.get_complaint(complaint_id))


@router.post(
    "/{complaint_id}/status",
    response_model=ComplaintDetailRead,
    summary="Start reviewing a complaint",
    description="The only legal move is submitted → in_review.",
)
async def start_complaint_review(
    complaint_id: UUID,
    payload: ComplaintStatusUpdate,
    service: ComplaintService = Depends(get_complaint_service),
) -> ComplaintDetailRead:
    return _detail(await service.start_review(complaint_id))


@router.post(
    "/{complaint_id}/response",
    response_model=ComplaintDetailRead,
    status_code=status.HTTP_201_CREATED,
    summary="Record the initial response to a complaint",
    description="A complaint accepts exactly one initial response and becomes answered.",
)
async def record_complaint_response(
    complaint_id: UUID,
    payload: ComplaintResponseRequest,
    service: ComplaintService = Depends(get_complaint_service),
    manager: User = Depends(require_roles(Role.MANAGER, Role.ADMIN)),
) -> ComplaintDetailRead:
    return _detail(
        await service.record_response(
            complaint_id, responder_id=manager.id, body=payload.body
        )
    )
