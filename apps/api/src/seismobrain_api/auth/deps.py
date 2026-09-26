"""
File: deps.py
Description: Resolve AuthPrincipal from Bearer JWT, API keys, or test headers
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-17
Modified: 2026-09-19
Version: 0.2.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from fastapi import HTTPException, Request

from seismobrain_api.container import AppContainer
from seismobrain_core.jwt_tokens import JwtKeyring, verify_jwt
from seismobrain_core.roles import SystemRole

_DEFAULT_KID = "default"
_API_KEY_PREFIX = "sbpat_"


@dataclass(frozen=True, slots=True)
class AuthPrincipal:
    user_id: str
    system_role: SystemRole
    email: str | None = None
    name: str | None = None
    credential: str = "jwt"  # "jwt" | "api_key" — never inferred by callers from scopes
    scopes: frozenset[str] | None = None  # granted scopes; None for non-API-key credentials


def _container(request: Request) -> AppContainer:
    return cast(AppContainer, request.app.state.container)


def resolve_principal(request: Request) -> AuthPrincipal:
    """Prefer Authorization Bearer; fall back to X-User-Id / X-System-Role for tests."""
    container = _container(request)
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth.removeprefix("Bearer ").strip()
        if not token:
            raise HTTPException(status_code=401, detail="authentication required")
        ring = JwtKeyring(
            keys={_DEFAULT_KID: container.settings.jwt_secret},
            active_kid=_DEFAULT_KID,
        )
        try:
            claims = verify_jwt(ring, token)
        except Exception as exc:  # noqa: BLE001 — map JWT errors for callers
            raise HTTPException(status_code=401, detail="invalid access token") from exc
        user_id = str(claims.get("sub", ""))
        if not user_id:
            raise HTTPException(status_code=401, detail="invalid access token")
        user = container.user_store.get_by_id(user_id)
        if user is None or user.status != "active":
            raise HTTPException(status_code=401, detail="authentication required")
        return AuthPrincipal(
            user_id=user.id,
            system_role=user.system_role,
            email=user.email,
            name=user.name,
        )

    user_id_header = request.headers.get("X-User-Id")
    role_raw = request.headers.get("X-System-Role", SystemRole.USER.value)
    try:
        role = SystemRole(role_raw)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="invalid system role") from exc
    # Test helpers historically sent X-System-Role alone for admin routes.
    if not user_id_header:
        if role is SystemRole.SYSTEM_ADMIN:
            return AuthPrincipal(user_id="test-admin", system_role=role)
        raise HTTPException(status_code=401, detail="authentication required")
    user = container.user_store.get_by_id(user_id_header)
    return AuthPrincipal(
        user_id=user_id_header,
        system_role=role,
        email=user.email if user else None,
        name=user.name if user else None,
    )


def resolve_scoped_principal(request: Request, *, required_scope: str) -> AuthPrincipal:
    """Like `resolve_principal`, but also accepts an `sbpat_` API key carrying
    `required_scope`. Only call this from routes explicitly enabled for API-key
    access (T04.1's scope table) — every other route stays on `resolve_principal`
    and is therefore API-key-blind by construction, not by a denylist.

    An `sbpat_` credential never falls back to JWT or test-helper headers: it is
    either accepted on its own or rejected outright.
    """
    auth = request.headers.get("Authorization", "")
    token = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else ""
    if not token.startswith(_API_KEY_PREFIX):
        return resolve_principal(request)

    container = _container(request)
    try:
        record = container.api_tokens.authenticate(token)
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail="invalid access token") from exc
    if required_scope not in record.scopes:
        raise HTTPException(status_code=403, detail="insufficient scope")
    # Current owner permissions, read fresh — never the scopes/role frozen at issue time.
    owner = container.user_store.get_by_id(record.owner_id)
    if owner is None or owner.status != "active":
        raise HTTPException(status_code=401, detail="authentication required")
    return AuthPrincipal(
        user_id=owner.id,
        system_role=owner.system_role,
        email=owner.email,
        name=owner.name,
        credential="api_key",
        scopes=record.scopes,
    )


def require_admin(request: Request) -> AuthPrincipal:
    principal = resolve_principal(request)
    if principal.system_role != SystemRole.SYSTEM_ADMIN:
        raise HTTPException(status_code=403, detail="admin only")
    return principal
