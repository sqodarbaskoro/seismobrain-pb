"""
File: test_jwt.py
Description: JWT minting/verification with kid and key rotation (SEC-03)
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
from jwt import InvalidTokenError

from seismobrain_core.jwt_tokens import JwtKeyring, mint_jwt, verify_jwt


def test_hs256_requires_256_bit_secret() -> None:
    with pytest.raises(ValueError, match="256"):
        JwtKeyring(keys={"k1": "too-short"}, active_kid="k1")


def test_mint_and_verify_includes_kid() -> None:
    secret = "a" * 64
    ring = JwtKeyring(keys={"k1": secret}, active_kid="k1")
    token = mint_jwt(ring, subject="user-1", ttl_seconds=900)
    header = __import__("jwt").get_unverified_header(token)
    assert header["kid"] == "k1"
    assert header["alg"] == "HS256"
    claims = verify_jwt(ring, token)
    assert claims["sub"] == "user-1"


def test_key_rotation_verifies_previous_kid() -> None:
    old = "b" * 64
    new = "c" * 64
    ring = JwtKeyring(keys={"old": old, "new": new}, active_kid="new")
    legacy = mint_jwt(
        JwtKeyring(keys={"old": old}, active_kid="old"),
        subject="user-2",
        ttl_seconds=900,
    )
    claims = verify_jwt(ring, legacy)
    assert claims["sub"] == "user-2"
    fresh = mint_jwt(ring, subject="user-3", ttl_seconds=900)
    assert __import__("jwt").get_unverified_header(fresh)["kid"] == "new"


def test_unknown_kid_rejected() -> None:
    ring = JwtKeyring(keys={"k1": "d" * 64}, active_kid="k1")
    other = mint_jwt(
        JwtKeyring(keys={"other": "e" * 64}, active_kid="other"),
        subject="x",
        ttl_seconds=60,
    )
    with pytest.raises(InvalidTokenError):
        verify_jwt(ring, other)
