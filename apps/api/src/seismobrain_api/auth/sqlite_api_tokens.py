"""
File: sqlite_api_tokens.py
Description: SQLite-backed API token store for Starter persistence (FR-AUTH-07)
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

import hashlib
import secrets
import sqlite3
import time
import uuid
from pathlib import Path

from seismobrain_api.auth.api_tokens import ApiTokenRecord


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


class SqliteApiTokenStore:
    """Persist API keys under DATA_DIR so Starter restarts don't invalidate them.

    First-upgrade note: keys issued before this store existed lived only in the
    in-process `InMemoryApiTokenStore` and are gone on the first restart after
    upgrading — there is no prior persisted state to migrate. Callers must issue
    new keys; no other data is affected.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS api_tokens (
                    id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    token_hash TEXT NOT NULL UNIQUE,
                    scopes TEXT NOT NULL,
                    expires_at INTEGER NOT NULL,
                    revoked_at INTEGER,
                    kind TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_api_tokens_owner ON api_tokens(owner_id)"
            )
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    def _row(self, row: sqlite3.Row) -> ApiTokenRecord:
        return ApiTokenRecord(
            id=row["id"],
            owner_id=row["owner_id"],
            name=row["name"],
            token_hash=row["token_hash"],
            scopes=frozenset(row["scopes"].split(",")) if row["scopes"] else frozenset(),
            expires_at=row["expires_at"],
            revoked_at=row["revoked_at"],
            kind=row["kind"],
        )

    def issue(
        self,
        *,
        owner_id: str,
        name: str,
        scopes: set[str],
        ttl_seconds: int,
        kind: str = "personal",
    ) -> tuple[ApiTokenRecord, str]:
        raw = f"sbpat_{secrets.token_urlsafe(24)}"
        record = ApiTokenRecord(
            id=f"tok_{uuid.uuid4().hex[:12]}",
            owner_id=owner_id,
            name=name,
            token_hash=_hash(raw),
            scopes=frozenset(scopes),
            expires_at=int(time.time()) + ttl_seconds,
            kind=kind,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO api_tokens
                    (id, owner_id, name, token_hash, scopes, expires_at, revoked_at, kind)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.owner_id,
                    record.name,
                    record.token_hash,
                    ",".join(sorted(record.scopes)),
                    record.expires_at,
                    record.revoked_at,
                    record.kind,
                ),
            )
            conn.commit()
        return record, raw

    def get(self, token_id: str) -> ApiTokenRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM api_tokens WHERE id = ?", (token_id,)
            ).fetchone()
        return self._row(row) if row else None

    def revoke(self, token_id: str) -> ApiTokenRecord:
        now = int(time.time())
        with self._connect() as conn:
            conn.execute(
                "UPDATE api_tokens SET revoked_at = ? WHERE id = ?", (now, token_id)
            )
            conn.commit()
        record = self.get(token_id)
        if record is None:
            raise KeyError(token_id)
        return record

    def delete(self, token_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM api_tokens WHERE id = ?", (token_id,))
            conn.commit()

    def list_for_owner(self, owner_id: str) -> list[ApiTokenRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM api_tokens WHERE owner_id = ? ORDER BY expires_at DESC",
                (owner_id,),
            ).fetchall()
        return [self._row(row) for row in rows]

    def authenticate(self, raw: str) -> ApiTokenRecord:
        digest = _hash(raw)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM api_tokens WHERE token_hash = ?", (digest,)
            ).fetchone()
        if row is None:
            raise PermissionError("invalid token")
        record = self._row(row)
        if record.revoked_at is not None:
            raise PermissionError("token revoked")
        if record.expires_at <= int(time.time()):
            raise PermissionError("token expired")
        return record
