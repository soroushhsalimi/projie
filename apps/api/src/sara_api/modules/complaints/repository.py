"""Complaint persistence. SQL lives here and nowhere above it (AGENTS.md §5)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from sara_api.modules.complaints.models import Complaint, ComplaintResponse
from sara_api.modules.users.models import User


class ComplaintRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_with_resident(
        self,
        *,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[tuple[Complaint, str]]:
        statement = (
            select(Complaint, User.full_name)
            .join(User, User.id == Complaint.resident_id)
            .order_by(Complaint.created_at.desc(), Complaint.id.desc())
            .limit(limit)
            .offset(offset)
        )
        if status is not None:
            statement = statement.where(Complaint.status == status)
        result = await self._session.execute(statement)
        return [(complaint, name) for complaint, name in result.all()]

    async def count(self, *, status: str | None) -> int:
        statement = select(func.count()).select_from(Complaint)
        if status is not None:
            statement = statement.where(Complaint.status == status)
        result = await self._session.execute(statement)
        return int(result.scalar_one())

    async def get_with_resident(self, complaint_id: UUID) -> tuple[Complaint, str] | None:
        result = await self._session.execute(
            select(Complaint, User.full_name)
            .join(User, User.id == Complaint.resident_id)
            .where(Complaint.id == complaint_id)
        )
        row = result.first()
        return (row[0], row[1]) if row is not None else None

    async def get_response(
        self, complaint_id: UUID
    ) -> tuple[ComplaintResponse, str] | None:
        result = await self._session.execute(
            select(ComplaintResponse, User.full_name)
            .join(User, User.id == ComplaintResponse.responder_id)
            .where(ComplaintResponse.complaint_id == complaint_id)
        )
        row = result.first()
        return (row[0], row[1]) if row is not None else None

    async def add_response(self, response: ComplaintResponse) -> ComplaintResponse:
        self._session.add(response)
        await self._session.flush()
        return response

    async def save(self, complaint: Complaint) -> Complaint:
        await self._session.flush()
        return complaint
