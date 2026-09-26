"""
File: sqlite_users.py
Description: SQLite-backed user store for Starter persistence
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-17
Modified: 2026-09-18
Version: 0.1.1
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path

from seismobrain_api.auth.users import UserRecord, UserStatus, hash_password
from seismobrain_core.roles import SystemRole


class SqliteUserStore:
    """Persist users under DATA_DIR so Starter survives process restarts."""

    def __init__(self, path: Path) -> None:
        self._path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    system_role TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    def _row(self, row: sqlite3.Row) -> UserRecord:
        return UserRecord(
            id=row["id"],
            email=row["email"],
            name=row["name"],
            password_hash=row["password_hash"],
            status=row["status"],
            system_role=SystemRole(row["system_role"]),
        )

    def create(
        self, *, email: str, name: str, password: str, status: UserStatus
    ) -> UserRecord:
        key = email.lower()
        if self.get_by_email(key) is not None:
            raise ValueError("email already registered")
        user = UserRecord(
            id=str(uuid.uuid4()),
            email=key,
            name=name,
            password_hash=hash_password(password),
            status=status,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO users (id, email, name, password_hash, status, system_role)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user.id,
                    user.email,
                    user.name,
                    user.password_hash,
                    user.status,
                    user.system_role.value,
                ),
            )
            conn.commit()
        return user

    def get_by_email(self, email: str) -> UserRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ?", (email.lower(),)
            ).fetchone()
        return self._row(row) if row else None

    def get_by_id(self, user_id: str) -> UserRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()
        return self._row(row) if row else None

    def update_password_hash(self, *, email: str, password_hash: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE email = ?",
                (password_hash, email.lower()),
            )
            conn.commit()

    def set_status(self, user_id: str, status: UserStatus) -> UserRecord:
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET status = ? WHERE id = ?", (status, user_id)
            )
            conn.commit()
        user = self.get_by_id(user_id)
        if user is None:
            raise KeyError(user_id)
        return user

    def set_system_role(self, user_id: str, role: SystemRole) -> UserRecord:
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET system_role = ? WHERE id = ?",
                (role.value, user_id),
            )
            conn.commit()
        user = self.get_by_id(user_id)
        if user is None:
            raise KeyError(user_id)
        return user

    def count(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()
        return int(row["n"]) if row else 0

    def list_users(self) -> list[UserRecord]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM users ORDER BY email").fetchall()
        return [self._row(row) for row in rows]
