"""
File: groups.py
Description: Groups API — list/detail, membership, and collection/document grants (FR-AUTH-05)
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

from typing import Literal, cast

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from seismobrain_api.auth.deps import require_admin
from seismobrain_api.container import AppContainer
from seismobrain_core.permissions import Permission

router = APIRouter(prefix="/api/v1/groups", tags=["groups"])


def _container(request: Request) -> AppContainer:
    return cast(AppContainer, request.app.state.container)


class CreateGroupBody(BaseModel):
    tenant_id: str = "default"
    name: str = Field(min_length=1)


class MemberBody(BaseModel):
    user_id: str


class GrantBody(BaseModel):
    resource_type: Literal["collection", "document"]
    resource_id: str
    permission: Literal["read", "write", "manage"]


_PERM = {
    "read": Permission.READ,
    "write": Permission.WRITE,
    "manage": Permission.MANAGE,
}
_PERM_NAME = {v: k for k, v in _PERM.items()}


@router.get("")
def list_groups(request: Request) -> dict[str, object]:
    require_admin(request)
    store = _container(request).groups
    return {
        "groups": [
            {
                "id": g.id,
                "name": g.name,
                "tenant_id": g.tenant_id,
                "member_count": len(g.member_ids),
            }
            for g in store.groups.values()
        ]
    }


@router.get("/grants")
def list_grants_for_resource(
    resource_type: Literal["collection", "document"], resource_id: str, request: Request
) -> dict[str, object]:
    """The team-grant half of a merged ACL view — pair with the collection's own
    direct-grant list (PUT /admin/collections/{id}/acl) for "who can access this".

    Registered before "/{group_id}" — otherwise a literal "/grants" path would be
    swallowed by that catch-all segment and never reach this handler."""
    require_admin(request)
    store = _container(request).groups
    grants = store.grants_for_resource(resource_type=resource_type, resource_id=resource_id)
    return {
        "grants": [
            {
                "group_id": group_id,
                "group_name": store.groups[group_id].name if group_id in store.groups else group_id,
                "permission": _PERM_NAME[perm],
            }
            for group_id, perm in grants.items()
        ]
    }


@router.get("/{group_id}")
def get_group(group_id: str, request: Request) -> dict[str, object]:
    require_admin(request)
    store = _container(request).groups
    group = store.groups.get(group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="group not found")
    return {
        "id": group.id,
        "name": group.name,
        "tenant_id": group.tenant_id,
        "members": sorted(group.member_ids),
    }


@router.post("", status_code=201)
def create_group(body: CreateGroupBody, request: Request) -> dict[str, str]:
    require_admin(request)
    record = _container(request).groups.create(
        tenant_id=body.tenant_id, name=body.name
    )
    return {"id": record.id, "name": record.name}


@router.post("/{group_id}/members")
def add_member(group_id: str, body: MemberBody, request: Request) -> dict[str, object]:
    require_admin(request)
    store = _container(request).groups
    if group_id not in store.groups:
        raise HTTPException(status_code=404, detail="group not found")
    store.add_member(group_id, body.user_id)
    members = sorted(store.groups[group_id].member_ids)
    return {"group_id": group_id, "user_id": body.user_id, "members": members}


@router.delete("/{group_id}/members/{user_id}")
def remove_member(group_id: str, user_id: str, request: Request) -> dict[str, object]:
    require_admin(request)
    store = _container(request).groups
    if group_id not in store.groups:
        raise HTTPException(status_code=404, detail="group not found")
    store.remove_member(group_id, user_id)
    return {"group_id": group_id, "members": sorted(store.groups[group_id].member_ids)}


@router.post("/{group_id}/grants")
def grant_permission(group_id: str, body: GrantBody, request: Request) -> dict[str, object]:
    require_admin(request)
    store = _container(request).groups
    if group_id not in store.groups:
        raise HTTPException(status_code=404, detail="group not found")
    store.grant(
        group_id=group_id,
        resource_type=body.resource_type,
        resource_id=body.resource_id,
        permission=_PERM[body.permission],
    )
    key = f"{body.resource_type}:{body.resource_id}"
    return {
        "group_id": group_id,
        "resource": key,
        "permission": body.permission,
        "vector_sync_ok": store.vector_sync_within_deadline(key),
    }


@router.delete("/{group_id}/grants")
def revoke_grant(
    group_id: str,
    resource_type: Literal["collection", "document"],
    resource_id: str,
    request: Request,
) -> dict[str, object]:
    require_admin(request)
    store = _container(request).groups
    if group_id not in store.groups:
        raise HTTPException(status_code=404, detail="group not found")
    store.revoke_grant(group_id=group_id, resource_type=resource_type, resource_id=resource_id)
    return {"group_id": group_id, "resource": f"{resource_type}:{resource_id}", "revoked": True}
