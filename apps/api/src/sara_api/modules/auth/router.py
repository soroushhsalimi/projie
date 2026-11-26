"""Authentication HTTP endpoints. No business rules live here."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status

from sara_api.api.deps import (
    ClientMeta,
    get_app_settings,
    get_auth_service,
    get_client_meta,
    get_current_user,
    require_trusted_origin,
)
from sara_api.core.config import Settings
from sara_api.modules.auth.schemas import LoginRequest, RegisterRequest, TokenResponse
from sara_api.modules.auth.service import AuthResult, AuthService
from sara_api.modules.users.models import User
from sara_api.modules.users.schemas import UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_refresh_cookie(response: Response, result: AuthResult, settings: Settings) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=result.refresh_token,
        max_age=settings.refresh_token_days * 24 * 60 * 60,
        path=settings.refresh_cookie_path,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )


def _clear_refresh_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path=settings.refresh_cookie_path,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )


def _token_response(result: AuthResult) -> TokenResponse:
    return TokenResponse(
        access_token=result.access_token,
        expires_in=result.expires_in,
        user=UserRead.model_validate(result.user),
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a resident account",
    description="Public registration. The role is always `user`; elevated accounts are provisioned by an admin.",
)
async def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_app_settings),
    meta: ClientMeta = Depends(get_client_meta),
) -> TokenResponse:
    result = await service.register(
        full_name=payload.full_name,
        email=str(payload.email),
        password=payload.password,
        national_id=payload.national_id,
        phone=payload.phone,
        address=payload.address,
        user_agent=meta.user_agent,
        ip=meta.ip,
    )
    _set_refresh_cookie(response, result, settings)
    return _token_response(result)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Sign in",
    description="Returns a short-lived access token and sets the rotating refresh cookie.",
)
async def login(
    payload: LoginRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_app_settings),
    meta: ClientMeta = Depends(get_client_meta),
) -> TokenResponse:
    result = await service.login(
        email=str(payload.email),
        password=payload.password,
        user_agent=meta.user_agent,
        ip=meta.ip,
    )
    _set_refresh_cookie(response, result, settings)
    return _token_response(result)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate the session",
    description="Consumes the refresh cookie, rotates it, and returns a new access token.",
    dependencies=[Depends(require_trusted_origin)],
)
async def refresh(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_app_settings),
    meta: ClientMeta = Depends(get_client_meta),
) -> TokenResponse:
    raw = request.cookies.get(settings.refresh_cookie_name)
    result = await service.refresh(raw, user_agent=meta.user_agent, ip=meta.ip)
    _set_refresh_cookie(response, result, settings)
    return _token_response(result)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Sign out",
    description="Revokes the refresh-token family and clears the cookie. Idempotent.",
    dependencies=[Depends(require_trusted_origin)],
)
async def logout(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_app_settings),
) -> Response:
    raw = request.cookies.get(settings.refresh_cookie_name)
    await service.logout(raw)
    _clear_refresh_cookie(response, settings)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get(
    "/me",
    response_model=UserRead,
    summary="Current principal",
    description="Returns the authenticated account's public profile.",
)
async def me(user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(user)
