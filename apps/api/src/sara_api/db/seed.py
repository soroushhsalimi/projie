"""Idempotent demo seed. Never runs automatically in production."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from sara_api.core.config import get_settings
from sara_api.core.security import PasswordHasher
from sara_api.db.base import Base
from sara_api.db.session import build_engine, build_session_factory
from sara_api.modules.complaints.models import Complaint, ComplaintResponse
from sara_api.modules.guests.models import GuestVisit
from sara_api.modules.tickets.models import Ticket, TicketMessage
from sara_api.modules.users.models import User

DEMO_ACCOUNTS = [
    (
        "resident@sara.ir",
        "Resident12345!",
        "سارا محمدی",
        "user",
        "0012345671",
        "09121234567",
        "تهران، خیابان آزادی، خوابگاه الزهرا",
    ),
    (
        "manager@sara.ir",
        "Manager12345!",
        "رضا کریمی",
        "manager",
        "0012345672",
        "09121234568",
        "تهران، خیابان کارگر، دفتر خوابگاه",
    ),
    (
        "admin@sara.ir",
        "Admin12345!",
        "مدیر سامانه",
        "admin",
        "0012345673",
        "09121234569",
        "تهران، خیابان ولیعصر، دفتر مرکزی",
    ),
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


# (subject, description, category, status, initial response by the manager or None)
DEMO_COMPLAINTS = [
    (
        "سر و صدای شبانه در طبقه سوم",
        "هر شب بعد از ساعت ۱۲ صدای بلند و رفت‌وآمد در راهروی طبقه سوم ادامه دارد.",
        "noise",
        "submitted",
        None,
    ),
    (
        "نظافت نکردن سرویس‌های بهداشتی",
        "سرویس‌های بهداشتی طبقه دوم دو روز است تمیز نشده‌اند.",
        "cleanliness",
        "in_review",
        None,
    ),
    (
        "خرابی چراغ راه‌پله اضطراری",
        "چراغ راه‌پلهٔ اضطراری بلوک ب خاموش است و شب‌ها مسیر خطرناک می‌شود.",
        "safety",
        "answered",
        "چراغ تعویض شد؛ لطفاً اگر دوباره خاموش شد اطلاع بدهید.",
    ),
]


# (guest_name, purpose, status, allowed_from, allowed_until, checked_in, checked_out)
# Offsets are relative to the seed run so the front desk always has a live window.
DEMO_GUESTS = [
    ("مریم احمدی", "ملاقات خانوادگی", "expected", -1, 3, None, None),
    ("حسین نوری", "تعمیر لوازم برقی", "checked_in", -2, 2, -1, None),
    ("زهرا کاظمی", "تحویل بسته", "checked_out", -8, -4, -7, -3),
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
        for email, password, full_name, role, national_id, phone, address in DEMO_ACCOUNTS:
            existing = await session.execute(select(User).where(User.email == email))
            if existing.scalar_one_or_none() is not None:
                continue
            session.add(
                User(
                    email=email,
                    password_hash=hasher.hash(password),
                    full_name=full_name,
                    national_id=national_id,
                    phone=phone,
                    address=address,
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

        complaint_count = await session.execute(select(func.count()).select_from(Complaint))
        if complaint_count.scalar_one() == 0:
            users = {
                user.email: user
                for user in (await session.execute(select(User))).scalars().all()
            }
            for subject, description, category, status, response_body in DEMO_COMPLAINTS:
                complaint = Complaint(
                    resident_id=users["resident@sara.ir"].id,
                    subject=subject,
                    description=description,
                    category=category,
                    status=status,
                )
                session.add(complaint)
                await session.flush()
                if response_body is not None:
                    session.add(
                        ComplaintResponse(
                            complaint_id=complaint.id,
                            responder_id=users["manager@sara.ir"].id,
                            body=response_body,
                        )
                    )
            created.append("demo complaints")

        guest_count = await session.execute(select(func.count()).select_from(GuestVisit))
        if guest_count.scalar_one() == 0:
            users = {
                user.email: user
                for user in (await session.execute(select(User))).scalars().all()
            }
            host = users["resident@sara.ir"]
            now = datetime.now(UTC)
            for (
                guest_name,
                purpose,
                status,
                from_hours,
                until_hours,
                in_hours,
                out_hours,
            ) in DEMO_GUESTS:
                session.add(
                    GuestVisit(
                        host_id=host.id,
                        guest_name=guest_name,
                        purpose=purpose,
                        allowed_from=now + timedelta(hours=from_hours),
                        allowed_until=now + timedelta(hours=until_hours),
                        status=status,
                        checked_in_at=(
                            now + timedelta(hours=in_hours) if in_hours is not None else None
                        ),
                        checked_out_at=(
                            now + timedelta(hours=out_hours) if out_hours is not None else None
                        ),
                    )
                )
            created.append("demo guest visits")

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
