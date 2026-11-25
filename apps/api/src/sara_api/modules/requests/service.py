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

from sara_api.core.errors import NotFound, RequestAlreadyActive, RequestWithdrawalBlocked
from sara_api.domain.requests import (
    RequestStatus,
    RoomType,
    WithdrawalNotAllowed,
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
