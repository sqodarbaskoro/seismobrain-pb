"""
File: test_metadata_store_sqlite.py
Description: SQLite Starter MetadataStore adapter tests
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

from pathlib import Path

import pytest

from seismobrain_adapters.metadata.sqlite import SqliteMetadataStore
from seismobrain_core.ports import MetadataStore


def test_sqlite_store_satisfies_port(tmp_path: Path) -> None:
    store: MetadataStore = SqliteMetadataStore(tmp_path / "meta.db")
    assert store.count_tenants() == 0
    tenant = store.create_tenant("Acme")
    assert tenant.name == "Acme"
    assert store.count_tenants() == 1
    fetched = store.get_tenant(tenant.id)
    assert fetched is not None
    assert fetched.id == tenant.id
    assert store.list_tenants() == [tenant]


def test_sqlite_store_persists_across_instances(tmp_path: Path) -> None:
    db = tmp_path / "meta.db"
    first = SqliteMetadataStore(db)
    tenant = first.create_tenant("Persisted")
    second = SqliteMetadataStore(db)
    assert second.get_tenant(tenant.id) == tenant


def test_create_tenant_rejects_blank_name(tmp_path: Path) -> None:
    store = SqliteMetadataStore(tmp_path / "meta.db")
    with pytest.raises(ValueError, match="name"):
        store.create_tenant("  ")
