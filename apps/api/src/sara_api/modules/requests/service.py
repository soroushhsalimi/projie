"""Accommodation-request use cases.

The service owns the unit of work (it never commits) and contains no FastAPI imports.
Ownership and the “one active request” invariant live here (SPEC-0005 FR-3).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from sara_api.core.errors import (
    NotFound,
    RequestAlreadyActive,
    RequestTransitionBlocked,
    RequestWithdrawalBlocked,
)
from sara_api.domain.requests import (
    RequestStatus,
    RequestTransitionNotAllowed,
    RoomType,
    WithdrawalNotAllowed,
    ensure_review_transition,
    ensure_withdrawable,
)
from sara_api.modules.requests.models import AccommodationRequest
from sara_api.modules.requests.repository import RequestRepository

logger = logging.getLogger("sara.requests")


@dataclass(frozen=True, slots=True)
class RequestPage:
    items: list[AccommodationRequest]
    total: int
    page: int
    per_page: int


@dataclass(frozen=True, slots=True)
class RequestQueueItem:
    request: AccommodationRequest
    applicant_name: str


@dataclass(frozen=True, slots=True)
class RequestQueuePage:
    items: list[RequestQueueItem]
    total: int
    page: int
    per_page: int


class RequestService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = RequestRepository(session)

    async def list_requests(
        self, applicant_id: UUID, *, page: int, per_page: int
    ) -> RequestPage:
        total = await self._repo.count_for_applicant(applicant_id)
        items = await self._repo.list_for_applicant(
            applicant_id, limit=per_page, offset=(page - 1) * per_page
        )
        return RequestPage(items=items, total=total, page=page, per_page=per_page)

    async def list_queue(
        self,
        *,
        status: RequestStatus | None,
        page: int,
        per_page: int,
    ) -> RequestQueuePage:
        status_value = status.value if status is not None else None
        total = await self._repo.count_queue(status=status_value)
        rows = await self._repo.list_queue(
            status=status_value,
            limit=per_page,
            offset=(page - 1) * per_page,
        )
        return RequestQueuePage(
            items=[
                RequestQueueItem(request=request, applicant_name=name)
                for request, name in rows
            ],
            total=total,
            page=page,
            per_page=per_page,
        )

    async def review(
        self, request_id: UUID, *, target: RequestStatus
    ) -> RequestQueueItem:
        row = await self._repo.get_with_applicant(request_id)
        if row is None:
            raise NotFound("Accommodation request not found.")
        request, applicant_name = row
        current = RequestStatus(request.status)
        try:
            ensure_review_transition(current, target)
        except RequestTransitionNotAllowed as exc:
            raise RequestTransitionBlocked(
                f"A request in status '{current}' cannot move to '{target}'."
            ) from exc
        request.status = target.value
        await self._repo.save(request)
        logger.info(
            "request.status.changed",
            extra={"request_id": str(request.id), "status": target.value},
        )
        return RequestQueueItem(request=request, applicant_name=applicant_name)

    async def submit(
        self,
        applicant_id: UUID,
        *,
        dormitory_name: str,
        room_type: RoomType,
        desired_move_in: date,
        duration_months: int,
        note: str | None,
    ) -> AccommodationRequest:
        if await self._repo.count_active(applicant_id) > 0:
            raise RequestAlreadyActive(
                "You already have an active accommodation request. Withdraw it first."
            )
        request = AccommodationRequest(
            applicant_id=applicant_id,
            dormitory_name=dormitory_name,
            room_type=room_type.value,
            desired_move_in=desired_move_in,
            duration_months=duration_months,
            note=note,
            status=RequestStatus.SUBMITTED.value,
        )
        await self._repo.add(request)
        logger.info(
            "request.submitted",
            extra={"request_id": str(request.id), "applicant_id": str(applicant_id)},
        )
        return request

    async def withdraw(self, applicant_id: UUID, request_id: UUID) -> AccommodationRequest:
        request = await self._repo.get_for_applicant(request_id, applicant_id)
        if request is None:
            raise NotFound("Accommodation request not found.")
        current = RequestStatus(request.status)
        try:
            ensure_withdrawable(current)
        except WithdrawalNotAllowed as exc:
            raise RequestWithdrawalBlocked(
                f"A request in status '{current}' cannot be withdrawn."
            ) from exc
        request.status = RequestStatus.WITHDRAWN.value
        await self._repo.save(request)
        logger.info(
            "request.withdrawn",
            extra={"request_id": str(request.id), "applicant_id": str(applicant_id)},
        )
        return request
