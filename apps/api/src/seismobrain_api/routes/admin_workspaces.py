"""
File: admin_workspaces.py
Description: Workspace and collection admin routes with ACL editor (FR-ADM-02)
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
from seismobrain_core.roles import WorkspaceRole

router = APIRouter(tags=["admin-workspaces"])


def _container(request: Request) -> AppContainer:
    return cast(AppContainer, request.app.state.container)


class NameBody(BaseModel):
    name: str = Field(min_length=1)


class AclBody(BaseModel):
    entries: list[dict[str, str]]


@router.get("/admin/workspaces")
def list_workspaces(request: Request) -> dict[str, object]:
    require_admin(request)
    items = [
        {"id": w.id, "name": w.name, "research_enabled": w.research_enabled}
        for w in _container(request).admin_catalog.workspaces.values()
    ]
    return {"workspaces": items}


@router.post("/admin/workspaces", status_code=201)
def create_workspace(body: NameBody, request: Request) -> dict[str, str]:
    principal = require_admin(request)
    container = _container(request)
    record = container.admin_catalog.create_workspace(
        body.name, actor=principal.user_id
    )
    container.collection_access.set_workspace_role(
        principal.user_id, record.id, WorkspaceRole.OWNER
    )
    return {"id": record.id, "name": record.name}


@router.post("/admin/workspaces/{workspace_id}/collections", status_code=201)
def create_collection(
    workspace_id: str, body: NameBody, request: Request
) -> dict[str, str]:
    principal = require_admin(request)
    container = _container(request)
    try:
        record = container.admin_catalog.create_collection(
            workspace_id=workspace_id, name=body.name, actor=principal.user_id
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="workspace not found") from exc
    container.collection_access.map_collection(record.id, workspace_id)
    container.collection_access.grant_write(principal.user_id, record.id)
    return {"id": record.id, "name": record.name, "workspace_id": record.workspace_id}


@router.get("/admin/workspaces/{workspace_id}/collections")
def list_collections(workspace_id: str, request: Request) -> dict[str, object]:
    require_admin(request)
    catalog = _container(request).admin_catalog
    if workspace_id not in catalog.workspaces:
        raise HTTPException(status_code=404, detail="workspace not found")
    items = [
        {
            "id": c.id,
            "name": c.name,
            "workspace_id": c.workspace_id,
            "acl": c.acl,
        }
        for c in catalog.collections.values()
        if c.workspace_id == workspace_id
    ]
    return {"collections": items}


def _principal_user_id(raw: str) -> str:
    if raw.startswith("user:"):
        return raw.removeprefix("user:")
    return raw


@router.put("/admin/collections/{collection_id}/acl")
def set_acl(collection_id: str, body: AclBody, request: Request) -> dict[str, object]:
    principal = require_admin(request)
    container = _container(request)
    try:
        record = container.admin_catalog.set_collection_acl(
            collection_id, body.entries, actor=principal.user_id
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="collection not found") from exc
    workspace_id = record.workspace_id
    container.collection_access.map_collection(collection_id, workspace_id)
    for entry in body.entries:
        user_id = _principal_user_id(
            entry.get("principal") or entry.get("user_id") or ""
        )
        if not user_id:
            continue
        perm = entry.get("permission", "read")
        container.collection_access.set_workspace_role(
            user_id, workspace_id, WorkspaceRole.MEMBER
        )
        if perm in {"write", "manage", "read_write"}:
            container.collection_access.grant_write(user_id, collection_id)
        else:
            container.collection_access.grant_read(user_id, collection_id)
    return {"id": record.id, "entries": record.acl}
