"""Guest-visit persistence. SQL lives here and nowhere above it (AGENTS.md §5)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from sara_api.modules.guests.models import GuestVisit
from sara_api.modules.users.models import User


class GuestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_with_host(
        self,
        *,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[tuple[GuestVisit, str]]:
        statement = (
            select(GuestVisit, User.full_name)
            .join(User, User.id == GuestVisit.host_id)
            .order_by(GuestVisit.created_at.desc(), GuestVisit.id.desc())
            .limit(limit)
            .offset(offset)
        )
        if status is not None:
            statement = statement.where(GuestVisit.status == status)
        result = await self._session.execute(statement)
        return [(visit, name) for visit, name in result.all()]

    async def count(self, *, status: str | None) -> int:
        statement = select(func.count()).select_from(GuestVisit)
        if status is not None:
            statement = statement.where(GuestVisit.status == status)
        result = await self._session.execute(statement)
        return int(result.scalar_one())

    async def get_with_host(self, visit_id: UUID) -> tuple[GuestVisit, str] | None:
        result = await self._session.execute(
            select(GuestVisit, User.full_name)
            .join(User, User.id == GuestVisit.host_id)
            .where(GuestVisit.id == visit_id)
        )
        row = result.first()
        return (row[0], row[1]) if row is not None else None

    async def find_resident_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(User).where(func.lower(User.email) == email.lower())
        )
        return result.scalar_one_or_none()

    async def add(self, visit: GuestVisit) -> GuestVisit:
        self._session.add(visit)
        await self._session.flush()
        return visit

    async def save(self, visit: GuestVisit) -> GuestVisit:
        await self._session.flush()
        return visit
