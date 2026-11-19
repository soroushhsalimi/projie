"""Integration test: the database itself enforces email uniqueness (SPEC-0002 FR-2, E1)."""

from __future__ import annotations

import pytest

from sara_api.core.errors import EmailAlreadyRegistered
from sara_api.modules.users.models import User
from sara_api.modules.users.repository import UserRepository


async def test_duplicate_email_raises_conflict(app) -> None:
    async with app.state.sessionmaker() as session:
        repository = UserRepository(session)
        await repository.add(
            User(
                email="ali@example.com",
                password_hash="$argon2id$fake",
                full_name="Ali",
                role="user",
                status="active",
            )
        )
        await session.commit()

    async with app.state.sessionmaker() as session:
        repository = UserRepository(session)
        with pytest.raises(EmailAlreadyRegistered):
            await repository.add(
                User(
                    email="ali@example.com",
                    password_hash="$argon2id$fake",
                    full_name="Other Ali",
                    role="user",
                    status="active",
                )
            )
