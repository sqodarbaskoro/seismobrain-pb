"""
File: auth.py
Description: Registration, token issuance, refresh, and SPA session routes (FR-AUTH-01/02)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-17
Version: 0.4.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from typing import Literal, cast

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field

from seismobrain_api.auth.deps import resolve_principal
from seismobrain_api.auth.tokens import (
    CSRF_HEADER,
    REFRESH_COOKIE_NAME,
    REFRESH_COOKIE_PATH,
    mint_access_token,
)
from seismobrain_api.auth.users import (
    PasswordPolicyError,
    UserStatus,
    hash_password,
    needs_rehash,
    verify_password,
)
from seismobrain_api.container import AppContainer
from seismobrain_api.rate_limit import client_ip, enforce_limit
from seismobrain_core.roles import SystemRole

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12)
    name: str = Field(min_length=1)


class RegisterResponse(BaseModel):
    id: str
    email: str
    status: UserStatus
    system_role: SystemRole


class TokenRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    csrf_token: str
    token_type: Literal["bearer"] = "bearer"


class AuthStatusResponse(BaseModel):
    has_users: bool
    registration_mode: Literal["approval", "closed", "open"]


class MeResponse(BaseModel):
    id: str
    email: str | None
    name: str | None
    system_role: SystemRole


def _container(request: Request) -> AppContainer:
    return cast(AppContainer, request.app.state.container)


def _cookie_secure(container: AppContainer) -> bool:
    return container.settings.public_url.startswith("https://")


def _set_refresh_cookie(
    response: Response,
    *,
    raw_token: str,
    max_age: int,
    secure: bool,
) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_token,
        max_age=max_age,
        httponly=True,
        secure=secure,
        samesite="strict",
        path=REFRESH_COOKIE_PATH,
    )


@router.get("/status", response_model=AuthStatusResponse)
def auth_status(request: Request) -> AuthStatusResponse:
    container = _container(request)
    return AuthStatusResponse(
        has_users=container.user_store.count() > 0,
        registration_mode=container.settings.registration_mode,
    )


@router.get("/me", response_model=MeResponse)
def me(request: Request) -> MeResponse:
    principal = resolve_principal(request)
    return MeResponse(
        id=principal.user_id,
        email=principal.email,
        name=principal.name,
        system_role=principal.system_role,
    )


@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(body: RegisterRequest, request: Request) -> RegisterResponse:
    container = _container(request)
    mode = container.settings.registration_mode
    if mode == "closed":
        raise HTTPException(status_code=403, detail="registration closed")
    bootstrap = container.user_store.count() == 0
    if bootstrap:
        status: UserStatus = "active"
    else:
        status = "active" if mode == "open" else "pending"
    try:
        user = container.user_store.create(
            email=str(body.email),
            name=body.name,
            password=body.password,
            status=status,
        )
    except PasswordPolicyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if bootstrap:
        user = container.user_store.set_system_role(user.id, SystemRole.SYSTEM_ADMIN)
    return RegisterResponse(
        id=user.id,
        email=user.email,
        status=user.status,
        system_role=user.system_role,
    )


@router.post("/token", response_model=TokenResponse)
def issue_token(
    body: TokenRequest, request: Request, response: Response
) -> TokenResponse:
    container = _container(request)
    email = str(body.email)
    ip = client_ip(request)
    enforce_limit(
        container,
        key=f"auth:ip:{ip}",
        limit=container.settings.auth_rate_limit_per_min,
        window_seconds=60,
    )
    enforce_limit(
        container,
        key=f"auth:account:{email.lower()}",
        limit=container.settings.auth_rate_limit_per_min,
        window_seconds=60,
    )
    remaining = container.account_lockout.remaining_delay(email)
    if remaining > 0:
        raise HTTPException(
            status_code=429,
            detail="account locked",
            headers={"Retry-After": str(int(remaining) if remaining >= 1 else 1)},
        )
    user = container.user_store.get_by_email(email)
    if user is None or not verify_password(body.password, user.password_hash):
        delay = container.account_lockout.record_failure(email)
        if delay > 0:
            raise HTTPException(
                status_code=429,
                detail="account locked",
                headers={"Retry-After": str(int(delay))},
            )
        raise HTTPException(status_code=401, detail="invalid credentials")
    if user.status == "pending":
        raise HTTPException(status_code=403, detail="pending approval")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="account disabled")
    container.account_lockout.record_success(email)
    if needs_rehash(user.password_hash):
        container.user_store.update_password_hash(
            email=user.email,
            password_hash=hash_password(body.password),
        )
    refresh = container.refresh_token_store.issue(
        user_id=user.id,
        ttl_days=container.settings.refresh_token_ttl_days,
        user_agent=request.headers.get("User-Agent", ""),
        ip=client_ip(request),
    )
    access = mint_access_token(
        user_id=user.id,
        secret=container.settings.jwt_secret,
        ttl_minutes=container.settings.access_token_ttl_min,
    )
    _set_refresh_cookie(
        response,
        raw_token=refresh.raw_token,
        max_age=container.settings.refresh_token_ttl_days * 86400,
        secure=_cookie_secure(container),
    )
    return TokenResponse(access_token=access, csrf_token=refresh.csrf_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: Request, response: Response) -> TokenResponse:
    container = _container(request)
    csrf = request.headers.get(CSRF_HEADER)
    if not csrf:
        raise HTTPException(status_code=403, detail="csrf required")
    raw = request.cookies.get(REFRESH_COOKIE_NAME)
    if not raw:
        raise HTTPException(status_code=401, detail="refresh cookie required")
    try:
        issued = container.refresh_token_store.rotate(
            raw_token=raw,
            csrf_token=csrf,
            ttl_days=container.settings.refresh_token_ttl_days,
        )
    except PermissionError as exc:
        detail = str(exc)
        if detail == "csrf mismatch":
            raise HTTPException(status_code=403, detail=detail) from exc
        raise HTTPException(status_code=401, detail=detail) from exc
    except LookupError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    access = mint_access_token(
        user_id=issued.user_id,
        secret=container.settings.jwt_secret,
        ttl_minutes=container.settings.access_token_ttl_min,
    )
    _set_refresh_cookie(
        response,
        raw_token=issued.raw_token,
        max_age=container.settings.refresh_token_ttl_days * 86400,
        secure=_cookie_secure(container),
    )
    return TokenResponse(access_token=access, csrf_token=issued.csrf_token)
