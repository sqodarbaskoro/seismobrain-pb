"""
File: test_envelope_encryption.py
Description: Envelope encryption for provider secrets (SEC-06)
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

from seismobrain_core.envelope import (
    EncryptedSecret,
    EnvelopeCipher,
    rotate_master_key,
)


def test_encrypt_decrypt_round_trip() -> None:
    master = "m" * 64
    cipher = EnvelopeCipher(master_key=master, key_id="k1")
    sealed = cipher.encrypt(b"provider-api-key")
    assert isinstance(sealed, EncryptedSecret)
    assert sealed.key_id == "k1"
    assert sealed.ciphertext != b"provider-api-key"
    assert cipher.decrypt(sealed) == b"provider-api-key"


def test_rotation_rewraps_with_new_key_id() -> None:
    old = "o" * 64
    new = "n" * 64
    sealed = EnvelopeCipher(master_key=old, key_id="old").encrypt(b"secret-value")
    rotated = rotate_master_key(sealed, old_master=old, new_master=new, new_key_id="new")
    assert rotated.key_id == "new"
    assert EnvelopeCipher(master_key=new, key_id="new").decrypt(rotated) == b"secret-value"
    with pytest.raises(ValueError):
        EnvelopeCipher(master_key=old, key_id="old").decrypt(rotated)
