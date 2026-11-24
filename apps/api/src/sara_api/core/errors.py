"""Expected error taxonomy shared by every layer.

This module deliberately imports no web framework: services and the domain may raise these errors
without depending on FastAPI (AGENTS.md §5.2). HTTP mapping lives in ``core.problem``.
"""

from __future__ import annotations

from http import HTTPStatus


class AppError(Exception):
    """Base class for expected, mapped errors."""

    code = "internal_error"
    status = HTTPStatus.INTERNAL_SERVER_ERROR
    title = "Internal server error"

    def __init__(self, detail: str | None = None, *, headers: dict[str, str] | None = None) -> None:
        self.detail = detail or self.title
        self.headers = headers or {}
        super().__init__(self.detail)


class ValidationFailed(AppError):
    code = "validation_error"
    status = HTTPStatus.UNPROCESSABLE_ENTITY
    title = "Request validation failed"


class EmailAlreadyRegistered(AppError):
    code = "email_already_registered"
    status = HTTPStatus.CONFLICT
    title = "Email already registered"


class InvalidCredentials(AppError):
    code = "invalid_credentials"
    status = HTTPStatus.UNAUTHORIZED
    title = "Invalid email or password"


class InvalidToken(AppError):
    code = "invalid_token"
    status = HTTPStatus.UNAUTHORIZED
    title = "Invalid or expired access token"


class InvalidSession(AppError):
    code = "invalid_session"
    status = HTTPStatus.UNAUTHORIZED
    title = "Invalid or expired session"


class OriginNotAllowed(AppError):
    code = "origin_not_allowed"
    status = HTTPStatus.FORBIDDEN
    title = "Origin not allowed"


class Forbidden(AppError):
    code = "forbidden"
    status = HTTPStatus.FORBIDDEN
    title = "You are not allowed to perform this action"


class NotFound(AppError):
    code = "not_found"
    status = HTTPStatus.NOT_FOUND
    title = "Resource not found"


class TicketTransitionBlocked(AppError):
    code = "ticket_transition_not_allowed"
    status = HTTPStatus.CONFLICT
    title = "Ticket status cannot change like that"


class NotReady(AppError):
    code = "not_ready"
    status = HTTPStatus.SERVICE_UNAVAILABLE
    title = "Service not ready"
