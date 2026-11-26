"""Complaint use cases.

The service owns the unit of work (it never commits) and contains no FastAPI imports. Role
enforcement happens in the transport layer; this layer owns existence, the status machine and the
answer-once rule.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from sara_api.core.errors import (
    ComplaintAlreadyAnsweredConflict,
    ComplaintTransitionBlocked,
    NotFound,
)
from sara_api.domain.complaints import (
    ComplaintAlreadyAnswered,
    ComplaintStatus,
    ComplaintTransitionNotAllowed,
    ensure_answerable,
    ensure_review_transition,
)
from sara_api.modules.complaints.models import Complaint, ComplaintResponse
from sara_api.modules.complaints.repository import ComplaintRepository

logger = logging.getLogger("sara.complaints")


@dataclass(frozen=True, slots=True)
class ComplaintListItem:
    complaint: Complaint
    resident_name: str


@dataclass(frozen=True, slots=True)
class ResponseRecord:
    response: ComplaintResponse
    responder_name: str


@dataclass(frozen=True, slots=True)
class ComplaintDetail:
    complaint: Complaint
    resident_name: str
    response: ResponseRecord | None


@dataclass(frozen=True, slots=True)
class ComplaintPage:
    items: list[ComplaintListItem]
    total: int
    page: int
    per_page: int


class ComplaintService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = ComplaintRepository(session)

    async def list_complaints(
        self,
        *,
        status: ComplaintStatus | None,
        page: int,
        per_page: int,
    ) -> ComplaintPage:
        status_value = status.value if status is not None else None
        total = await self._repo.count(status=status_value)
        rows = await self._repo.list_with_resident(
            status=status_value,
            limit=per_page,
            offset=(page - 1) * per_page,
        )
        return ComplaintPage(
            items=[
                ComplaintListItem(complaint=complaint, resident_name=name)
                for complaint, name in rows
            ],
            total=total,
            page=page,
            per_page=per_page,
        )

    async def get_complaint(self, complaint_id: UUID) -> ComplaintDetail:
        complaint, resident_name = await self._require(complaint_id)
        return await self._detail(complaint, resident_name)

    async def start_review(self, complaint_id: UUID) -> ComplaintDetail:
        complaint, resident_name = await self._require(complaint_id)
        current = ComplaintStatus(complaint.status)
        try:
            ensure_review_transition(current, ComplaintStatus.IN_REVIEW)
        except ComplaintTransitionNotAllowed as exc:
            raise ComplaintTransitionBlocked(
                f"A complaint in status '{current}' cannot move to "
                f"'{ComplaintStatus.IN_REVIEW}'."
            ) from exc
        complaint.status = ComplaintStatus.IN_REVIEW.value
        await self._repo.save(complaint)
        logger.info(
            "complaint.status.changed",
            extra={"complaint_id": str(complaint.id), "status": ComplaintStatus.IN_REVIEW.value},
        )
        return await self._detail(complaint, resident_name)

    async def record_response(
        self, complaint_id: UUID, *, responder_id: UUID, body: str
    ) -> ComplaintDetail:
        complaint, resident_name = await self._require(complaint_id)
        current = ComplaintStatus(complaint.status)
        try:
            ensure_answerable(current)
        except ComplaintAlreadyAnswered as exc:
            raise ComplaintAlreadyAnsweredConflict(
                "This complaint already has an initial response."
            ) from exc
        await self._repo.add_response(
            ComplaintResponse(
                complaint_id=complaint.id,
                responder_id=responder_id,
                body=body.strip(),
            )
        )
        complaint.status = ComplaintStatus.ANSWERED.value
        await self._repo.save(complaint)
        logger.info(
            "complaint.response.recorded",
            extra={"complaint_id": str(complaint.id), "status": complaint.status},
        )
        return await self._detail(complaint, resident_name)

    async def _require(self, complaint_id: UUID) -> tuple[Complaint, str]:
        row = await self._repo.get_with_resident(complaint_id)
        if row is None:
            raise NotFound("Complaint not found.")
        return row

    async def _detail(self, complaint: Complaint, resident_name: str) -> ComplaintDetail:
        row = await self._repo.get_response(complaint.id)
        record: ResponseRecord | None = None
        if row is not None:
            response, responder_name = row
            record = ResponseRecord(response=response, responder_name=responder_name)
        return ComplaintDetail(
            complaint=complaint,
            resident_name=resident_name,
            response=record,
        )
