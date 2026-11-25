"""Accommodation-request persistence. Resident queries are scoped to the applicant."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from sara_api.domain.requests import ACTIVE_STATUSES
from sara_api.modules.requests.models import AccommodationRequest
from sara_api.modules.users.models import User


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
                AccommodationRequest.status.in_([status.value for status in ACTIVE_STATUSES]),
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

    def _with_applicant(self) -> Select[tuple[AccommodationRequest, str]]:
        return select(AccommodationRequest, User.full_name).join(
            User, User.id == AccommodationRequest.applicant_id
        )

    async def list_queue(
        self, *, status: str | None, limit: int, offset: int
    ) -> list[tuple[AccommodationRequest, str]]:
        """Return ``(request, applicant_name)`` for the manager queue, newest first."""
        statement = (
            self._with_applicant()
            .order_by(
                AccommodationRequest.created_at.desc(), AccommodationRequest.id.desc()
            )
            .limit(limit)
            .offset(offset)
        )
        if status is not None:
            statement = statement.where(AccommodationRequest.status == status)
        result = await self._session.execute(statement)
        return [(request, name) for request, name in result.all()]

    async def count_queue(self, *, status: str | None) -> int:
        statement = select(func.count()).select_from(AccommodationRequest)
        if status is not None:
            statement = statement.where(AccommodationRequest.status == status)
        result = await self._session.execute(statement)
        return int(result.scalar_one())

    async def get_with_applicant(
        self, request_id: UUID
    ) -> tuple[AccommodationRequest, str] | None:
        result = await self._session.execute(
            self._with_applicant().where(AccommodationRequest.id == request_id)
        )
        row = result.first()
        return (row[0], row[1]) if row is not None else None

    async def add(self, request: AccommodationRequest) -> AccommodationRequest:
        self._session.add(request)
        await self._session.flush()
        return request

    async def save(self, request: AccommodationRequest) -> AccommodationRequest:
        await self._session.flush()
        return request
