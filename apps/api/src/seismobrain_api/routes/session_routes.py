"""
File: session_routes.py
Description: Self-service "your active sessions" list and per-device sign-out (FR-AUTH-10)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-17
Version: 0.2.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from typing import cast

from fastapi import APIRouter, HTTPException, Request

from seismobrain_api.auth.deps import resolve_principal
from seismobrain_api.container import AppContainer

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


def _container(request: Request) -> AppContainer:
    return cast(AppContainer, request.app.state.container)


@router.get("")
def list_sessions(request: Request) -> dict[str, object]:
    """Each row is a refresh-token family — the same thing an admin's force-sign-out
    (admin_users.py) revokes in bulk. There's no separate "current session" marker
    since we don't track which family issued this request's access token."""
    principal = resolve_principal(request)
    items = _container(request).refresh_token_store.list_sessions_for_user(principal.user_id)
    return {
        "sessions": [
            {
                "id": s.family_id,
                "created_at": s.created_at,
                "user_agent": s.user_agent,
                "ip": s.ip,
            }
            for s in items
        ]
    }


@router.post("/{session_id}/revoke")
def revoke_session(session_id: str, request: Request) -> dict[str, object]:
    principal = resolve_principal(request)
    try:
        _container(request).refresh_token_store.revoke_family(
            session_id, user_id=principal.user_id
        )
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"id": session_id, "revoked": True}
