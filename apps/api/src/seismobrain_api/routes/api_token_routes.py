"""
File: api_token_routes.py
Description: Personal/service API token management routes (FR-AUTH-07)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-19
Version: 0.3.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from typing import Literal, cast

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from seismobrain_api.auth.deps import resolve_principal
from seismobrain_api.container import AppContainer
from seismobrain_core.principal_epoch import PrincipalSet, bump_principal_authz_epochs

router = APIRouter(prefix="/api/v1/api-tokens", tags=["api-tokens"])

# T04.1's frozen scope table only ever checks "read". A key can't be issued with
# any other scope, and older keys issued before this validation existed simply
# never match `required_scope` on any route — their unsupported scope strings
# grant nothing, they're just inert.
_MAX_TTL_SECONDS = 60 * 60 * 24 * 90  # 90 days — matches the website's key lifetime


def _container(request: Request) -> AppContainer:
    return cast(AppContainer, request.app.state.container)


def _user_id(request: Request) -> str:
    return resolve_principal(request).user_id


class IssueBody(BaseModel):
    name: str = Field(min_length=1)
    scopes: list[Literal["read"]] = Field(min_length=1)
    ttl_seconds: int = Field(default=3600, gt=0, le=_MAX_TTL_SECONDS)
    kind: Literal["personal", "service"] = "personal"


@router.get("")
def list_tokens(request: Request) -> dict[str, object]:
    """Never includes the raw token — that's shown once, at issue time, only."""
    user_id = _user_id(request)
    items = _container(request).api_tokens.list_for_owner(user_id)
    return {
        "tokens": [
            {
                "id": t.id,
                "name": t.name,
                "scopes": sorted(t.scopes),
                "expires_at": t.expires_at,
                "kind": t.kind,
                "revoked": t.revoked_at is not None,
            }
            for t in items
        ]
    }


@router.post("", status_code=201)
def issue_token(body: IssueBody, request: Request) -> dict[str, object]:
    user_id = _user_id(request)
    record, raw = _container(request).api_tokens.issue(
        owner_id=user_id,
        name=body.name,
        scopes=set(body.scopes),
        ttl_seconds=body.ttl_seconds,
        kind=body.kind,
    )
    return {
        "id": record.id,
        "token": raw,
        "scopes": sorted(record.scopes),
        "expires_at": record.expires_at,
        "kind": record.kind,
    }


def _remove(token_id: str, request: Request, *, delete: bool) -> dict[str, object]:
    user_id = _user_id(request)
    store = _container(request).api_tokens
    record = store.get(token_id)
    if record is None or record.owner_id != user_id:
        raise HTTPException(status_code=404, detail="not found")
    if delete:
        store.delete(token_id)
    else:
        store.revoke(token_id)
    # Bump principal epoch for owner (FR-ACL-12 / T4.6).
    oidc = _container(request).oidc
    if user_id not in oidc.principals:
        oidc.principals[user_id] = PrincipalSet(
            user_id=user_id, group_ids=frozenset(), epoch=0
        )
    oidc.principals = bump_principal_authz_epochs(
        oidc.principals, changed_user_id=user_id
    )
    return {"id": token_id, "epoch": oidc.principals[user_id].epoch}


@router.post("/{token_id}/revoke")
def revoke_token(token_id: str, request: Request) -> dict[str, object]:
    return {**_remove(token_id, request, delete=False), "revoked": True}


@router.delete("/{token_id}")
def delete_token(token_id: str, request: Request) -> dict[str, object]:
    return {**_remove(token_id, request, delete=True), "deleted": True}


@router.post("/authenticate")
def authenticate_token(request: Request) -> dict[str, object]:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="bearer required")
    scope = request.headers.get("X-Required-Scope", "read")
    try:
        record = _container(request).api_tokens.authenticate(
            auth.removeprefix("Bearer ").strip()
        )
        if scope not in record.scopes:
            raise PermissionError("scope denied")
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return {"owner_id": record.owner_id, "scopes": sorted(record.scopes)}
