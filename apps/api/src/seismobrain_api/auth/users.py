"""
File: users.py
Description: In-memory user store for registration and token issuance (M0b)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-17
Version: 0.4.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Literal, Protocol

from seismobrain_core.password import (
    PasswordPolicyError,
    hash_password,
    needs_rehash,
    verify_password,
)
from seismobrain_core.roles import SystemRole

UserStatus = Literal["pending", "active", "disabled"]

__all__ = [
    "InMemoryUserStore",
    "PasswordPolicyError",
    "UserRecord",
    "UserStatus",
    "UserStore",
    "hash_password",
    "needs_rehash",
    "verify_password",
]


@dataclass
class UserRecord:
    id: str
    email: str
    name: str
    password_hash: str
    status: UserStatus
    system_role: SystemRole = SystemRole.USER


class UserStore(Protocol):
    def create(
        self, *, email: str, name: str, password: str, status: UserStatus
    ) -> UserRecord: ...

    def get_by_email(self, email: str) -> UserRecord | None: ...

    def get_by_id(self, user_id: str) -> UserRecord | None: ...

    def update_password_hash(self, *, email: str, password_hash: str) -> None: ...

    def set_status(self, user_id: str, status: UserStatus) -> UserRecord: ...

    def set_system_role(self, user_id: str, role: SystemRole) -> UserRecord: ...

    def count(self) -> int: ...

    def list_users(self) -> list[UserRecord]: ...


class InMemoryUserStore:
    def __init__(self) -> None:
        self._by_email: dict[str, UserRecord] = {}
        self._by_id: dict[str, UserRecord] = {}

    def create(
        self, *, email: str, name: str, password: str, status: UserStatus
    ) -> UserRecord:
        key = email.lower()
        if key in self._by_email:
            raise ValueError("email already registered")
        user = UserRecord(
            id=str(uuid.uuid4()),
            email=key,
            name=name,
            password_hash=hash_password(password),
            status=status,
        )
        self._by_email[key] = user
        self._by_id[user.id] = user
        return user

    def get_by_email(self, email: str) -> UserRecord | None:
        return self._by_email.get(email.lower())

    def get_by_id(self, user_id: str) -> UserRecord | None:
        return self._by_id.get(user_id)

    def update_password_hash(self, *, email: str, password_hash: str) -> None:
        user = self._by_email[email.lower()]
        user.password_hash = password_hash

    def set_status(self, user_id: str, status: UserStatus) -> UserRecord:
        user = self._by_id[user_id]
        user.status = status
        return user

    def set_system_role(self, user_id: str, role: SystemRole) -> UserRecord:
        user = self._by_id[user_id]
        user.system_role = role
        return user

    def count(self) -> int:
        return len(self._by_id)

    def list_users(self) -> list[UserRecord]:
        return sorted(self._by_id.values(), key=lambda u: u.email)
