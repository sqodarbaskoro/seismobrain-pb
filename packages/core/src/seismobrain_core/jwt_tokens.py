"""
File: jwt_tokens.py
Description: JWT mint/verify with kid and key rotation (SEC-03)
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

import time
from dataclasses import dataclass
from typing import Any

import jwt


@dataclass(frozen=True)
class JwtKeyring:
    """HS256 keyring with active kid; prior kids remain valid for verify."""

    keys: dict[str, str]
    active_kid: str

    def __post_init__(self) -> None:
        if self.active_kid not in self.keys:
            raise ValueError("active_kid must be present in keys")
        for kid, secret in self.keys.items():
            # ≥256-bit secret (32 bytes); accept ≥64 hex/ascii chars as PRD default.
            if len(secret.encode()) < 32:
                raise ValueError(
                    f"JWT secret for kid={kid!r} must be ≥256-bit (≥32 bytes)"
                )


def mint_jwt(
    keyring: JwtKeyring,
    *,
    subject: str,
    ttl_seconds: int,
    now: int | None = None,
) -> str:
    issued_at = int(time.time()) if now is None else now
    payload = {
        "sub": subject,
        "iat": issued_at,
        "exp": issued_at + ttl_seconds,
    }
    return jwt.encode(
        payload,
        keyring.keys[keyring.active_kid],
        algorithm="HS256",
        headers={"kid": keyring.active_kid},
    )


def verify_jwt(keyring: JwtKeyring, token: str) -> dict[str, Any]:
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    if not isinstance(kid, str) or kid not in keyring.keys:
        raise jwt.InvalidTokenError("unknown or missing kid")
    return jwt.decode(token, keyring.keys[kid], algorithms=["HS256"])
