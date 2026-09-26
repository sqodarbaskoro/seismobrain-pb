"""
File: catalog_hydrate.py
Description: Rebuild collection_access grants from persisted admin catalog at startup
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-17
Modified: 2026-09-17
Version: 0.1.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from seismobrain_api.admin_catalog import AdminCatalog
from seismobrain_api.auth.users import UserStore
from seismobrain_api.collection_access import InMemoryCollectionAccessStore
from seismobrain_api.sqlite_admin_catalog import SqliteAdminCatalog
from seismobrain_core.roles import SystemRole, WorkspaceRole


def hydrate_collection_access(
    *,
    catalog: AdminCatalog | SqliteAdminCatalog,
    access: InMemoryCollectionAccessStore,
    user_store: UserStore,
) -> None:
    """Map collections and grant owners/admins write so Starter survives restart."""
    admins = [
        u
        for u in user_store.list_users()
        if u.system_role is SystemRole.SYSTEM_ADMIN and u.status == "active"
    ]
    for collection in catalog.collections.values():
        access.map_collection(collection.id, collection.workspace_id)
        for admin in admins:
            access.set_workspace_role(
                admin.id, collection.workspace_id, WorkspaceRole.OWNER
            )
            access.grant_write(admin.id, collection.id)
        for entry in collection.acl:
            raw = entry.get("principal") or entry.get("user_id") or ""
            user_id = raw.removeprefix("user:") if raw.startswith("user:") else raw
            perm = entry.get("permission", "read")
            if not user_id:
                continue
            access.set_workspace_role(
                user_id, collection.workspace_id, WorkspaceRole.MEMBER
            )
            if perm in {"write", "manage", "read_write"}:
                access.grant_write(user_id, collection.id)
            else:
                access.grant_read(user_id, collection.id)
