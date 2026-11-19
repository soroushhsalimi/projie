"""HTTP mapping for expected errors and the RFC 9457 response factory."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from sara_api.core.errors import AppError, ValidationFailed

logger = logging.getLogger("sara.errors")

PROBLEM_BASE = "https://sara.local/errors"
PROBLEM_MEDIA_TYPE = "application/problem+json"


def problem_body(request: Request, code: str, title: str, status: int, detail: str) -> dict[str, Any]:
    return {
        "type": f"{PROBLEM_BASE}/{code.replace('_', '-')}",
        "title": title,
        "status": status,
        "code": code,
        "detail": detail,
        "instance": request.url.path,
    }


def problem_response(
    request: Request,
    *,
    code: str,
    title: str,
    status: int,
    detail: str,
    headers: dict[str, str] | None = None,
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    body = problem_body(request, code, title, status, detail)
    if extra:
        body.update(extra)
    response_headers = {"Cache-Control": "no-store"}
    if headers:
        response_headers.update(headers)
    return JSONResponse(
        status_code=status,
        content=body,
        media_type=PROBLEM_MEDIA_TYPE,
        headers=response_headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError) -> JSONResponse:
        headers = dict(exc.headers)
        if exc.status == HTTPStatus.UNAUTHORIZED and "WWW-Authenticate" not in headers:
            headers["WWW-Authenticate"] = "Bearer"
        return problem_response(
            request,
            code=exc.code,
            title=exc.title,
            status=int(exc.status),
            detail=exc.detail,
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        fields = []
        for error in exc.errors():
            location = [str(part) for part in error.get("loc", []) if part != "body"]
            fields.append(
                {
                    "field": ".".join(location) or "body",
                    "message": error.get("msg", "Invalid value"),
                    "type": error.get("type", "value_error"),
                }
            )
        return problem_response(
            request,
            code=ValidationFailed.code,
            title=ValidationFailed.title,
            status=int(ValidationFailed.status),
            detail="One or more fields are invalid.",
            extra={"errors": fields},
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "not_found" if exc.status_code == 404 else "http_error"
        title = "Resource not found" if exc.status_code == 404 else "Request failed"
        return problem_response(
            request,
            code=code,
            title=title,
            status=exc.status_code,
            detail=str(exc.detail),
            headers={"Allow": exc.headers["allow"]} if exc.headers and "allow" in exc.headers else None,
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.exception(
            "unhandled_exception",
            extra={"request_id": request_id, "path": request.url.path},
        )
        return problem_response(
            request,
            code="internal_error",
            title="Internal server error",
            status=500,
            detail="An unexpected error occurred. Quote the request id if you contact support.",
        )
