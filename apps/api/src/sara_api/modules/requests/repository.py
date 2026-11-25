"""Accommodation-request persistence. Every query is scoped to the applicant."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from sara_api.domain.requests import RequestStatus
from sara_api.modules.requests.models import AccommodationRequest


class RequestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_applicant(
        self, applicant_id: UUID, *, limit: int, offset: int
    ) -> list[AccommodationRequest]:
        result = await self._session.execute(
            select(AccommodationRequest)
            .where(AccommodationRequest.applicant_id == applicant_id)
            .order_by(AccommodationRequest.created_at.desc(), AccommodationRequest.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count_for_applicant(self, applicant_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(AccommodationRequest)
            .where(AccommodationRequest.applicant_id == applicant_id)
        )
        return int(result.scalar_one())

    async def count_active(self, applicant_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(AccommodationRequest)
            .where(
                AccommodationRequest.applicant_id == applicant_id,
                AccommodationRequest.status == RequestStatus.SUBMITTED.value,
            )
        )
        return int(result.scalar_one())

    async def get_for_applicant(
        self, request_id: UUID, applicant_id: UUID
    ) -> AccommodationRequest | None:
        result = await self._session.execute(
            select(AccommodationRequest).where(
                AccommodationRequest.id == request_id,
                AccommodationRequest.applicant_id == applicant_id,
            )
        )
        return result.scalar_one_or_none()

    async def add(self, request: AccommodationRequest) -> AccommodationRequest:
        self._session.add(request)
        await self._session.flush()
        return request

    async def save(self, request: AccommodationRequest) -> AccommodationRequest:
        await self._session.flush()
        return request
