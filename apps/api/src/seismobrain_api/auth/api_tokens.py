"""
File: api_tokens.py
Description: Scoped expiring revocable API tokens (FR-AUTH-07)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-19
Version: 0.3.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import hashlib
import secrets
import time
import uuid
from dataclasses import dataclass, field
from typing import Protocol


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


@dataclass
class ApiTokenRecord:
    id: str
    owner_id: str
    name: str
    token_hash: str
    scopes: frozenset[str]
    expires_at: int
    revoked_at: int | None = None
    kind: str = "personal"  # personal | service


class ApiTokenStore(Protocol):
    """Smallest interface issue/lookup/list/revoke needs; SQLite persists it for
    Starter restarts (T04.3), the in-memory dataclass below backs tests."""

    def issue(
        self,
        *,
        owner_id: str,
        name: str,
        scopes: set[str],
        ttl_seconds: int,
        kind: str = "personal",
    ) -> tuple[ApiTokenRecord, str]: ...

    def get(self, token_id: str) -> ApiTokenRecord | None: ...

    def revoke(self, token_id: str) -> ApiTokenRecord: ...

    def delete(self, token_id: str) -> None: ...

    def list_for_owner(self, owner_id: str) -> list[ApiTokenRecord]: ...

    def authenticate(self, raw: str) -> ApiTokenRecord:
        """Return the record for a valid, unexpired, unrevoked secret.

        Raises PermissionError("invalid token" | "token revoked" | "token expired")
        otherwise. Scope is a route-policy decision, not this store's — callers
        check `required_scope in record.scopes` themselves.
        """
        ...


@dataclass
class InMemoryApiTokenStore:
    tokens: dict[str, ApiTokenRecord] = field(default_factory=dict)

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
        self.tokens[record.id] = record
        return record, raw

    def get(self, token_id: str) -> ApiTokenRecord | None:
        return self.tokens.get(token_id)

    def revoke(self, token_id: str) -> ApiTokenRecord:
        record = self.tokens[token_id]
        record.revoked_at = int(time.time())
        return record

    def delete(self, token_id: str) -> None:
        self.tokens.pop(token_id, None)

    def list_for_owner(self, owner_id: str) -> list[ApiTokenRecord]:
        return sorted(
            (t for t in self.tokens.values() if t.owner_id == owner_id),
            key=lambda t: t.expires_at,
            reverse=True,
        )

    def authenticate(self, raw: str) -> ApiTokenRecord:
        digest = _hash(raw)
        now = int(time.time())
        for record in self.tokens.values():
            if record.token_hash != digest:
                continue
            if record.revoked_at is not None:
                raise PermissionError("token revoked")
            if record.expires_at <= now:
                raise PermissionError("token expired")
            return record
        raise PermissionError("invalid token")
