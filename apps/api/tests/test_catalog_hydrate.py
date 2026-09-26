"""
File: test_catalog_hydrate.py
Description: Hydrate collection_access from persisted catalog for Starter restart
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

from pathlib import Path

from seismobrain_api.auth.users import InMemoryUserStore
from seismobrain_api.catalog_hydrate import hydrate_collection_access
from seismobrain_api.collection_access import InMemoryCollectionAccessStore
from seismobrain_api.sqlite_admin_catalog import SqliteAdminCatalog
from seismobrain_core.roles import SystemRole


def test_hydrate_grants_admin_write(tmp_path: Path) -> None:
    users = InMemoryUserStore()
    admin = users.create(
        email="admin@example.com",
        name="Admin",
        password="long-enough-pass",
        status="active",
    )
    users.set_system_role(admin.id, SystemRole.SYSTEM_ADMIN)
    catalog = SqliteAdminCatalog(tmp_path / "catalog.db")
    ws = catalog.create_workspace("Ops", actor=admin.id)
    col = catalog.create_collection(workspace_id=ws.id, name="docs", actor=admin.id)

    access = InMemoryCollectionAccessStore()
    hydrate_collection_access(catalog=catalog, access=access, user_store=users)
    assert access.can_read_collection(admin.id, col.id)
    assert access.list_collections(admin.id) == [col.id]
