"""
File: tokens.py
Description: Access tokens and rotating refresh-token families (FR-AUTH-02, SEC-04)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-17
Version: 0.2.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
import uuid
from dataclasses import dataclass, field
from typing import Protocol

from seismobrain_core.jwt_tokens import JwtKeyring, mint_jwt, verify_jwt

REFRESH_COOKIE_NAME = "sb_refresh"
REFRESH_COOKIE_PATH = "/auth"
CSRF_HEADER = "X-CSRF-Token"
_DEFAULT_KID = "default"


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def mint_access_token(
    *,
    user_id: str,
    secret: str,
    ttl_minutes: int,
    kid: str = _DEFAULT_KID,
    keyring: JwtKeyring | None = None,
) -> str:
    """Mint a short-lived JWT access token (≤15 min)."""
    if ttl_minutes > 15:
        raise ValueError("access token TTL must be ≤15 minutes")
    ring = keyring or JwtKeyring(keys={kid: secret}, active_kid=kid)
    return mint_jwt(ring, subject=user_id, ttl_seconds=ttl_minutes * 60)


def access_token_ttl_seconds(
    token: str,
    secret: str,
    *,
    kid: str = _DEFAULT_KID,
    keyring: JwtKeyring | None = None,
) -> int:
    """Return remaining lifetime in seconds; raises ValueError if invalid."""
    ring = keyring or JwtKeyring(keys={kid: secret}, active_kid=kid)
    try:
        claims = verify_jwt(ring, token)
    except Exception as exc:  # noqa: BLE001 — map JWT errors for callers
        raise ValueError("invalid access token") from exc
    return int(claims["exp"]) - int(time.time())


@dataclass
class RefreshIssue:
    raw_token: str
    csrf_token: str
    family_id: str
    user_id: str
    expires_at: int


@dataclass
class _RefreshRecord:
    id: str
    user_id: str
    family_id: str
    token_hash: str
    csrf_hash: str
    expires_at: int
    revoked_at: int | None = None
    superseded: bool = False
    user_agent: str = ""
    ip: str = ""


@dataclass(frozen=True, slots=True)
class SessionInfo:
    """One row for a "your active sessions" self-service page — a refresh-token
    family, the same thing `admin_users.py` force-signs-out by the dozen."""

    family_id: str
    created_at: int
    user_agent: str
    ip: str


class RefreshTokenStore(Protocol):
    def issue(
        self,
        *,
        user_id: str,
        ttl_days: int,
        family_id: str | None = None,
        user_agent: str = "",
        ip: str = "",
    ) -> RefreshIssue: ...

    def rotate(self, *, raw_token: str, csrf_token: str, ttl_days: int) -> RefreshIssue: ...

    def family_revoked(self, family_id: str) -> bool: ...

    def revoke_all_for_user(self, user_id: str) -> int: ...

    def list_sessions_for_user(self, user_id: str) -> list[SessionInfo]: ...

    def revoke_family(self, family_id: str, *, user_id: str) -> None: ...


@dataclass
class InMemoryRefreshTokenStore:
    """In-memory refresh tokens with family reuse detection."""

    _by_hash: dict[str, _RefreshRecord] = field(default_factory=dict)
    _revoked_families: set[str] = field(default_factory=set)
    # A family's *first* issue time — carried across rotations, so "signed in
    # since" reflects the original login, not the last silent token refresh.
    _family_created_at: dict[str, int] = field(default_factory=dict)

    def issue(
        self,
        *,
        user_id: str,
        ttl_days: int,
        family_id: str | None = None,
        user_agent: str = "",
        ip: str = "",
    ) -> RefreshIssue:
        family = family_id or str(uuid.uuid4())
        raw = secrets.token_urlsafe(32)
        csrf = secrets.token_urlsafe(32)
        expires_at = int(time.time()) + ttl_days * 86400
        record = _RefreshRecord(
            id=str(uuid.uuid4()),
            user_id=user_id,
            family_id=family,
            token_hash=_hash_token(raw),
            csrf_hash=_hash_token(csrf),
            expires_at=expires_at,
            user_agent=user_agent,
            ip=ip,
        )
        self._by_hash[record.token_hash] = record
        self._family_created_at.setdefault(family, int(time.time()))
        return RefreshIssue(
            raw_token=raw,
            csrf_token=csrf,
            family_id=family,
            user_id=user_id,
            expires_at=expires_at,
        )

    def rotate(self, *, raw_token: str, csrf_token: str, ttl_days: int) -> RefreshIssue:
        token_hash = _hash_token(raw_token)
        record = self._by_hash.get(token_hash)
        if record is None:
            raise LookupError("unknown refresh token")
        if record.family_id in self._revoked_families or record.revoked_at is not None:
            raise PermissionError("family revoked")
        if record.superseded:
            self._revoke_family(record.family_id)
            raise PermissionError("refresh token reuse")
        if record.expires_at < int(time.time()):
            raise LookupError("expired refresh token")
        if not hmac.compare_digest(record.csrf_hash, _hash_token(csrf_token)):
            raise PermissionError("csrf mismatch")
        record.superseded = True
        return self.issue(
            user_id=record.user_id,
            ttl_days=ttl_days,
            family_id=record.family_id,
            user_agent=record.user_agent,
            ip=record.ip,
        )

    def list_sessions_for_user(self, user_id: str) -> list[SessionInfo]:
        """One row per active family: the current (non-superseded, non-revoked)
        token in that chain, i.e. exactly what a signed-in device holds right now."""
        sessions = [
            SessionInfo(
                family_id=r.family_id,
                created_at=self._family_created_at.get(r.family_id, r.expires_at),
                user_agent=r.user_agent,
                ip=r.ip,
            )
            for r in self._by_hash.values()
            if r.user_id == user_id and not r.superseded and r.revoked_at is None
        ]
        return sorted(sessions, key=lambda s: s.created_at, reverse=True)

    def revoke_family(self, family_id: str, *, user_id: str) -> None:
        owns = any(
            r.family_id == family_id and r.user_id == user_id
            for r in self._by_hash.values()
        )
        if not owns:
            raise PermissionError("session not found")
        self._revoke_family(family_id)

    def family_revoked(self, family_id: str) -> bool:
        return family_id in self._revoked_families

    def revoke_all_for_user(self, user_id: str) -> int:
        families = {
            record.family_id
            for record in self._by_hash.values()
            if record.user_id == user_id
        }
        for family_id in families:
            self._revoke_family(family_id)
        return len(families)

    def _revoke_family(self, family_id: str) -> None:
        self._revoked_families.add(family_id)
        now = int(time.time())
        for record in self._by_hash.values():
            if record.family_id == family_id:
                record.revoked_at = now
