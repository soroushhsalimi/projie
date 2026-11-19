"""Contract tests for the RFC 9457 error model (SPEC-0001 FR-3, FR-4)."""

from __future__ import annotations


async def test_unknown_route_returns_problem_json(client) -> None:
    response = await client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert set(body) == {"type", "title", "status", "code", "detail", "instance"}
    assert body["code"] == "not_found"
    assert body["instance"] == "/api/v1/does-not-exist"


async def test_unhandled_exception_hides_internal_details(app, client) -> None:
    @app.get("/boom")
    async def boom() -> None:
        raise RuntimeError("secret internal detail")

    response = await client.get("/boom")
    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "internal_error"
    assert "secret internal detail" not in response.text
    assert "Traceback" not in response.text
