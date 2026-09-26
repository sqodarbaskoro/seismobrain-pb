"""
File: password.py
Description: Password policy validation and Argon2id hashing (FR-AUTH-03, SEC-02)
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

import hashlib
import secrets

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

# OWASP Password Storage Cheat Sheet — interactive login baseline.
ARGON2_TIME_COST = 2
ARGON2_MEMORY_COST = 19456  # KiB (~19 MiB)
ARGON2_PARALLELISM = 1
_MIN_LENGTH = 12
_LEGACY_PREFIX = "sha256$"
_LEGACY_SALT = "sb-dev-salt"

# Small local breached-password denylist (common choices ≥12 chars).
_BREACHED_PASSWORDS = frozenset(
    {
        "password1234",
        "password12345",
        "123456789012",
        "qwertyuiop12",
        "letmein12345",
        "changeme1234",
        "adminpassword",
        "welcome12345",
    }
)

_HASHER = PasswordHasher(
    time_cost=ARGON2_TIME_COST,
    memory_cost=ARGON2_MEMORY_COST,
    parallelism=ARGON2_PARALLELISM,
    type=Type.ID,
)


class PasswordPolicyError(ValueError):
    """Raised when a password fails policy checks."""


def validate_password(password: str) -> None:
    if len(password) < _MIN_LENGTH:
        raise PasswordPolicyError("password length must be at least 12")
    if password.lower() in _BREACHED_PASSWORDS or password in _BREACHED_PASSWORDS:
        raise PasswordPolicyError("password appears in breached-password list")


def hash_password(password: str) -> str:
    validate_password(password)
    return _HASHER.hash(password)


def hash_password_legacy(password: str) -> str:
    """SHA256 placeholder used before Argon2id; kept for rehash tests."""
    digest = hashlib.sha256(f"{_LEGACY_SALT}:{password}".encode()).hexdigest()
    return f"{_LEGACY_PREFIX}{digest}"


def verify_password(password: str, password_hash: str) -> bool:
    if password_hash.startswith(_LEGACY_PREFIX):
        expected = hash_password_legacy(password)
        return secrets.compare_digest(expected, password_hash)
    try:
        return _HASHER.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    if password_hash.startswith(_LEGACY_PREFIX):
        return True
    try:
        return _HASHER.check_needs_rehash(password_hash)
    except InvalidHashError:
        return True
