"""
File: test_sqlite_users.py
Description: SQLite user store persistence for Starter
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

from seismobrain_api.auth.sqlite_users import SqliteUserStore
from seismobrain_core.roles import SystemRole


def test_sqlite_user_store_persists_across_instances(tmp_path: Path) -> None:
    path = tmp_path / "users.db"
    store = SqliteUserStore(path)
    user = store.create(
        email="a@example.com",
        name="A",
        password="long-enough-pass",
        status="active",
    )
    store.set_system_role(user.id, SystemRole.SYSTEM_ADMIN)
    assert store.count() == 1

    reopened = SqliteUserStore(path)
    found = reopened.get_by_email("a@example.com")
    assert found is not None
    assert found.id == user.id
    assert found.system_role is SystemRole.SYSTEM_ADMIN
    assert reopened.count() == 1
