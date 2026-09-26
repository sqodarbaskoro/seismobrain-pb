"""
File: admin_users.py
Description: Admin user management endpoints (FR-ADM-01)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-16
Version: 0.1.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from typing import cast

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from seismobrain_api.auth.deps import require_admin
from seismobrain_api.container import AppContainer
from seismobrain_core.roles import SystemRole

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


def _container(request: Request) -> AppContainer:
    return cast(AppContainer, request.app.state.container)


class RoleBody(BaseModel):
    system_role: SystemRole


@router.get("")
def list_users(request: Request) -> dict[str, object]:
    require_admin(request)
    users = _container(request).user_store.list_users()
    return {
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "name": u.name,
                "status": u.status,
                "system_role": u.system_role.value,
            }
            for u in users
        ]
    }


@router.post("/{user_id}/approve")
def approve_user(user_id: str, request: Request) -> dict[str, str]:
    require_admin(request)
    user = _container(request).user_store.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="not found")
    updated = _container(request).user_store.set_status(user_id, "active")
    return {"id": updated.id, "status": updated.status}


@router.post("/{user_id}/disable")
def disable_user(user_id: str, request: Request) -> dict[str, str]:
    require_admin(request)
    user = _container(request).user_store.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="not found")
    updated = _container(request).user_store.set_status(user_id, "disabled")
    _container(request).refresh_token_store.revoke_all_for_user(user_id)
    return {"id": updated.id, "status": updated.status}


@router.post("/{user_id}/role")
def set_role(user_id: str, body: RoleBody, request: Request) -> dict[str, str]:
    require_admin(request)
    user = _container(request).user_store.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="not found")
    updated = _container(request).user_store.set_system_role(user_id, body.system_role)
    return {"id": updated.id, "system_role": updated.system_role.value}


@router.post("/{user_id}/sessions/revoke")
def revoke_sessions(user_id: str, request: Request) -> dict[str, int]:
    require_admin(request)
    user = _container(request).user_store.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="not found")
    count = _container(request).refresh_token_store.revoke_all_for_user(user_id)
    return {"revoked_families": count}
