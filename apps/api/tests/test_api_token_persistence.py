"""
File: test_api_token_persistence.py
Description: SQLite API-token persistence across restarts/processes (FR-AUTH-07)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-19
Modified: 2026-09-19
Version: 0.1.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from seismobrain_api.auth.sqlite_api_tokens import SqliteApiTokenStore


def test_issued_and_revoked_state_visible_from_a_separate_connection(tmp_path: Path) -> None:
    db = tmp_path / "api_tokens.db"
    writer = SqliteApiTokenStore(db)
    record, raw = writer.issue(owner_id="u1", name="ci", scopes={"read"}, ttl_seconds=3600)

    reader = SqliteApiTokenStore(db)  # separate connection/process stand-in
    found = reader.authenticate(raw)
    assert found.id == record.id
    assert found.owner_id == "u1"

    writer.revoke(record.id)
    reader2 = SqliteApiTokenStore(db)
    try:
        reader2.authenticate(raw)
        raise AssertionError("expected PermissionError after revoke")
    except PermissionError as exc:
        assert "revoked" in str(exc)


def test_reopening_storage_preserves_keys(tmp_path: Path) -> None:
    db = tmp_path / "api_tokens.db"
    store = SqliteApiTokenStore(db)
    store.issue(owner_id="u1", name="ci", scopes={"read"}, ttl_seconds=3600)
    del store

    reopened = SqliteApiTokenStore(db)  # simulates process restart
    tokens = reopened.list_for_owner("u1")
    assert len(tokens) == 1
    assert tokens[0].name == "ci"


def test_raw_secret_is_never_persisted(tmp_path: Path) -> None:
    db = tmp_path / "api_tokens.db"
    store = SqliteApiTokenStore(db)
    _, raw = store.issue(owner_id="u1", name="ci", scopes={"read"}, ttl_seconds=3600)

    with sqlite3.connect(db) as conn:
        rows = conn.execute("SELECT * FROM api_tokens").fetchall()
    flattened = [str(v) for row in rows for v in row]
    assert raw not in flattened


def test_additive_migration_preserves_existing_rows_on_reopen(tmp_path: Path) -> None:
    """The table is created with CREATE TABLE IF NOT EXISTS: reopening a store that
    already has rows must never drop or truncate them."""
    db = tmp_path / "api_tokens.db"
    first = SqliteApiTokenStore(db)
    first.issue(owner_id="u1", name="one", scopes={"read"}, ttl_seconds=3600)

    second = SqliteApiTokenStore(db)  # re-runs schema setup against the same file
    second.issue(owner_id="u1", name="two", scopes={"read"}, ttl_seconds=3600)

    assert {t.name for t in second.list_for_owner("u1")} == {"one", "two"}
