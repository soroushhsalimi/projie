"""Schema-level guarantee: timestamps cross the API boundary as UTC with an explicit marker."""

from __future__ import annotations

import uuid
from datetime import datetime

from sara_api.modules.users.schemas import UserRead


def test_naive_database_timestamp_is_serialized_as_utc() -> None:
    user = UserRead(
        id=uuid.uuid4(),
        email="ali@example.com",
        full_name="Ali",
        role="user",
        status="active",
        created_at=datetime(2026, 1, 1, 12, 0, 0),
    )

    payload = user.model_dump(mode="json")

    assert payload["created_at"] == "2026-01-01T12:00:00Z"
