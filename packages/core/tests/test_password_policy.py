"""
File: test_password_policy.py
Description: Password policy and Argon2id hashing tests (FR-AUTH-03, SEC-02)
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

import pytest
from argon2 import PasswordHasher
from argon2.low_level import Type

from seismobrain_core.password import (
    ARGON2_MEMORY_COST,
    ARGON2_PARALLELISM,
    ARGON2_TIME_COST,
    PasswordPolicyError,
    hash_password,
    hash_password_legacy,
    needs_rehash,
    validate_password,
    verify_password,
)


def test_rejects_short_and_breached_passwords() -> None:
    with pytest.raises(PasswordPolicyError, match="length"):
        validate_password("short")
    with pytest.raises(PasswordPolicyError, match="breached"):
        validate_password("password1234")
    validate_password("unique-enough-passphrase")


def test_argon2id_parameters_and_verify() -> None:
    digest = hash_password("unique-enough-passphrase")
    assert digest.startswith("$argon2id$")
    assert verify_password("unique-enough-passphrase", digest) is True
    assert verify_password("wrong-password!!", digest) is False
    assert needs_rehash(digest) is False
    assert ARGON2_TIME_COST == 2
    assert ARGON2_MEMORY_COST == 19456
    assert ARGON2_PARALLELISM == 1
    ph = PasswordHasher(
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_COST,
        parallelism=ARGON2_PARALLELISM,
        type=Type.ID,
    )
    assert ph.check_needs_rehash(digest) is False


def test_legacy_hash_verifies_and_needs_rehash() -> None:
    legacy = hash_password_legacy("unique-enough-passphrase")
    assert legacy.startswith("sha256$")
    assert verify_password("unique-enough-passphrase", legacy) is True
    assert needs_rehash(legacy) is True
    upgraded = hash_password("unique-enough-passphrase")
    assert needs_rehash(upgraded) is False
