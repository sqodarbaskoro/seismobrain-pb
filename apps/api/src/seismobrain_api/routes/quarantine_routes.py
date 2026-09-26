"""
File: quarantine_routes.py
Description: Quarantine list/inspect/release routes, admin-only (FR-ING-06)
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
from pydantic import BaseModel, Field

from seismobrain_api.auth.deps import require_admin
from seismobrain_api.container import AppContainer
from seismobrain_api.quarantine import QuarantineItem

router = APIRouter(prefix="/api/v1", tags=["quarantine"])


def _container(request: Request) -> AppContainer:
    return cast(AppContainer, request.app.state.container)


class QuarantineBody(BaseModel):
    filename: str
    reason: str = Field(min_length=1)


def _public(item: QuarantineItem) -> dict[str, object]:
    return {
        "id": item.id,
        "filename": item.filename,
        "reason": item.reason,
        "status": item.status,
        "created_at": item.created_at,
    }


@router.get("/quarantine")
def list_quarantine(request: Request) -> dict[str, object]:
    require_admin(request)
    items = _container(request).quarantine.list_pending()
    return {"items": [_public(item) for item in items]}


@router.post("/quarantine", status_code=201)
def quarantine_file(body: QuarantineBody, request: Request) -> dict[str, object]:
    require_admin(request)
    item = _container(request).quarantine.quarantine(
        filename=body.filename, reason=body.reason
    )
    return _public(item)


@router.get("/quarantine/{item_id}")
def inspect_quarantine(item_id: str, request: Request) -> dict[str, object]:
    require_admin(request)
    try:
        item = _container(request).quarantine.inspect(item_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="not found") from exc
    return _public(item)


@router.post("/quarantine/{item_id}/release")
def release_quarantine(item_id: str, request: Request) -> dict[str, object]:
    principal = require_admin(request)
    try:
        item = _container(request).quarantine.release(item_id, actor=principal.user_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="not found") from exc
    return {"id": item.id, "status": item.status}
