"""Idempotent demo seed. Never runs automatically in production."""

from __future__ import annotations

import asyncio

from sqlalchemy import func, select

from sara_api.core.config import get_settings
from sara_api.core.security import PasswordHasher
from sara_api.db.base import Base
from sara_api.db.session import build_engine, build_session_factory
from sara_api.modules.tickets.models import Ticket, TicketMessage
from sara_api.modules.users.models import User

DEMO_ACCOUNTS = [
    ("resident@sara.ir", "Resident12345!", "سارا محمدی", "user"),
    ("manager@sara.ir", "Manager12345!", "رضا کریمی", "manager"),
    ("admin@sara.ir", "Admin12345!", "مدیر سامانه", "admin"),
]

# (subject, description, category, status, [(author_email, body), ...])
DEMO_TICKETS = [
    (
        "نشتی شیر آب حمام طبقه دوم",
        "از دیشب آب از شیر حمام طبقه دوم چکه می‌کند و کف راهرو خیس شده است.",
        "plumbing",
        "open",
        [
            ("resident@sara.ir", "سلام، لطفاً هرچه زودتر بررسی کنید؛ کف راهرو خیس است."),
        ],
    ),
    (
        "خرابی بخاری اتاق ۲۰۴",
        "بخاری اتاق ۲۰۴ روشن نمی‌شود و دمای اتاق پایین است.",
        "heating",
        "under_review",
        [
            ("resident@sara.ir", "بخاری دیشب کامل خاموش شد."),
            ("manager@sara.ir", "تعمیرکار برای فردا صبح هماهنگ شد."),
        ],
    ),
    (
        "شکستگی تخت خواب بلوک ب",
        "پایهٔ تخت خواب شمارهٔ ۱۲ لق شده و خطرناک است.",
        "furniture",
        "resolved",
        [
            ("resident@sara.ir", "تخت لق شده و صدای بدی می‌دهد."),
            ("manager@sara.ir", "پایه تعویض شد. اگر مشکلی بود دوباره تیکت بزنید."),
        ],
    ),
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
        await session.flush()

        ticket_count = await session.execute(select(func.count()).select_from(Ticket))
        if ticket_count.scalar_one() == 0:
            users = {
                user.email: user
                for user in (await session.execute(select(User))).scalars().all()
            }
            for subject, description, category, status, messages in DEMO_TICKETS:
                reporter = users["resident@sara.ir"]
                ticket = Ticket(
                    reporter_id=reporter.id,
                    subject=subject,
                    description=description,
                    category=category,
                    status=status,
                )
                session.add(ticket)
                await session.flush()
                for author_email, body in messages:
                    author = users[author_email]
                    session.add(
                        TicketMessage(ticket_id=ticket.id, author_id=author.id, body=body)
                    )
            created.append("demo tickets")

        await session.commit()

    await engine.dispose()
    return created


def main() -> None:
    created = asyncio.run(seed())
    if created:
        print("Seeded:")
        for item in created:
            print(f"  - {item}")
    else:
        print("Seed already applied; nothing to do.")


if __name__ == "__main__":
    main()
