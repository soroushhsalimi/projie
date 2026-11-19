"""Idempotent demo seed. Never runs automatically in production."""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from sara_api.core.config import get_settings
from sara_api.core.security import PasswordHasher
from sara_api.db.base import Base
from sara_api.db.session import build_engine, build_session_factory
from sara_api.modules.users.models import User

DEMO_ACCOUNTS = [
    ("resident@sara.ir", "Resident12345!", "سارا محمدی", "user"),
    ("manager@sara.ir", "Manager12345!", "رضا کریمی", "manager"),
    ("admin@sara.ir", "Admin12345!", "مدیر سامانه", "admin"),
]


async def seed() -> list[str]:
    settings = get_settings()
    engine = build_engine(settings)
    session_factory = build_session_factory(engine)
    hasher = PasswordHasher()
    created: list[str] = []

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        for email, password, full_name, role in DEMO_ACCOUNTS:
            existing = await session.execute(select(User).where(User.email == email))
            if existing.scalar_one_or_none() is not None:
                continue
            session.add(
                User(
                    email=email,
                    password_hash=hasher.hash(password),
                    full_name=full_name,
                    role=role,
                    status="active",
                )
            )
            created.append(email)
        await session.commit()

    await engine.dispose()
    return created


def main() -> None:
    created = asyncio.run(seed())
    if created:
        print("Seeded accounts:")
        for email in created:
            print(f"  - {email}")
    else:
        print("Seed already applied; nothing to do.")


if __name__ == "__main__":
    main()
