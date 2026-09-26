"""
File: test_starter_single_tenant.py
Description: Starter tier refuses creating a second tenant (FR-ACL-01)
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
from seismobrain_adapters.metadata.starter import StarterSingleTenantMetadataStore


def test_starter_refuses_second_tenant(tmp_path: Path) -> None:
    inner = SqliteMetadataStore(tmp_path / "meta.db")
    store = StarterSingleTenantMetadataStore(inner)
    store.create_tenant("Only")
    with pytest.raises(ValueError, match="single tenant"):
        store.create_tenant("Another")
    assert store.count_tenants() == 1
