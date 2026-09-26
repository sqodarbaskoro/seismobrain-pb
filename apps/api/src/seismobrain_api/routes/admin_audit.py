"""
File: admin_audit.py
Description: Append-only audit log list/export endpoints (FR-ADM-07)
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

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import PlainTextResponse

from seismobrain_api.container import AppContainer
from seismobrain_core.roles import SystemRole

router = APIRouter(prefix="/admin/audit", tags=["admin-audit"])


def _container(request: Request) -> AppContainer:
    return cast(AppContainer, request.app.state.container)


def _require_admin(request: Request) -> None:
    if request.headers.get("X-System-Role") != SystemRole.SYSTEM_ADMIN.value:
        raise HTTPException(status_code=403, detail="admin only")


@router.get("")
def list_audit(request: Request, action: str | None = None) -> dict[str, object]:
    _require_admin(request)
    items = _container(request).admin_catalog.audit
    if action:
        items = [entry for entry in items if entry.action == action]
    return {
        "items": [
            {
                "id": entry.id,
                "action": entry.action,
                "actor": entry.actor,
                "detail": entry.detail,
                "created_at": entry.created_at,
            }
            for entry in items
        ]
    }


@router.get("/export")
def export_audit(request: Request, action: str | None = None) -> PlainTextResponse:
    _require_admin(request)
    items = _container(request).admin_catalog.audit
    if action:
        items = [entry for entry in items if entry.action == action]
    lines = [
        f"{entry.created_at}\t{entry.action}\t{entry.actor}\t{entry.detail}"
        for entry in items
    ]
    return PlainTextResponse("\n".join(lines) + ("\n" if lines else ""))


@router.delete("/{entry_id}")
def delete_audit(entry_id: str, request: Request) -> Response:
    _require_admin(request)
    raise HTTPException(status_code=405, detail="audit log is append-only")
