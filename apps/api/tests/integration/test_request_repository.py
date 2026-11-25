"""Integration tests for accommodation-request persistence (SPEC-0005 FR-3, FR-4)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from sara_api.modules.requests.models import AccommodationRequest
from sara_api.modules.requests.repository import RequestRepository
from sara_api.modules.users.models import User

BASE = datetime(2026, 11, 20, 8, 0, tzinfo=UTC)


async def _user(session, email: str) -> User:  # type: ignore[no-untyped-def]
    user = User(
        email=email,
        password_hash="x",
        full_name=email.split("@", 1)[0],
        role="user",
        status="active",
    )
    session.add(user)
    await session.flush()
    return user


def _request(applicant_id, **overrides):  # type: ignore[no-untyped-def]
    values = {
        "applicant_id": applicant_id,
        "dormitory_name": "خوابگاه الزهرا",
        "room_type": "double",
        "desired_move_in": date(2027, 2, 1),
        "duration_months": 6,
        "note": None,
        "status": "submitted",
    }
    values.update(overrides)
    return AccommodationRequest(**values)


async def test_list_is_applicant_scoped_and_newest_first(app) -> None:
    async with app.state.sessionmaker() as session:
        resident = await _user(session, "resident@example.com")
        neighbour = await _user(session, "neighbour@example.com")
        repository = RequestRepository(session)
        await repository.add(_request(resident.id, note="older", created_at=BASE, updated_at=BASE))
        await repository.add(
            _request(
                resident.id,
                note="newer",
                created_at=BASE + timedelta(hours=1),
                updated_at=BASE + timedelta(hours=1),
            )
        )
        await repository.add(_request(neighbour.id, note="someone else"))
        await session.flush()

        rows = await repository.list_for_applicant(resident.id, limit=10, offset=0)

        assert [row.note for row in rows] == ["newer", "older"]
        assert await repository.count_for_applicant(resident.id) == 2


async def test_active_count_ignores_withdrawn_requests(app) -> None:
    async with app.state.sessionmaker() as session:
        resident = await _user(session, "resident@example.com")
        repository = RequestRepository(session)
        await repository.add(_request(resident.id, status="withdrawn"))
        await session.flush()

        assert await repository.count_active(resident.id) == 0

        await repository.add(_request(resident.id))
        await session.flush()

        assert await repository.count_active(resident.id) == 1


async def test_get_for_applicant_hides_foreign_requests(app) -> None:
    async with app.state.sessionmaker() as session:
        resident = await _user(session, "resident@example.com")
        neighbour = await _user(session, "neighbour@example.com")
        repository = RequestRepository(session)
        stored = await repository.add(_request(neighbour.id))
        await session.flush()

        assert await repository.get_for_applicant(stored.id, neighbour.id) is not None
        assert await repository.get_for_applicant(stored.id, resident.id) is None
