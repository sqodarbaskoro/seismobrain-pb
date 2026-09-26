"""
File: envelope.py
Description: Envelope encryption for provider secrets with key IDs (SEC-06)
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
import os
from dataclasses import dataclass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


@dataclass(frozen=True)
class EncryptedSecret:
    key_id: str
    nonce: bytes
    ciphertext: bytes


class EnvelopeCipher:
    """AES-GCM envelope using a derived key from the master key + key_id."""

    def __init__(self, *, master_key: str, key_id: str) -> None:
        if len(master_key) < 32:
            raise ValueError("master_key must be at least 32 characters")
        if not key_id:
            raise ValueError("key_id required")
        self._key_id = key_id
        self._key = hashlib.sha256(f"{master_key}:{key_id}".encode()).digest()

    def encrypt(self, plaintext: bytes) -> EncryptedSecret:
        nonce = os.urandom(12)
        ciphertext = AESGCM(self._key).encrypt(nonce, plaintext, None)
        return EncryptedSecret(key_id=self._key_id, nonce=nonce, ciphertext=ciphertext)

    def decrypt(self, secret: EncryptedSecret) -> bytes:
        if secret.key_id != self._key_id:
            raise ValueError("key_id mismatch")
        return AESGCM(self._key).decrypt(secret.nonce, secret.ciphertext, None)


def rotate_master_key(
    secret: EncryptedSecret,
    *,
    old_master: str,
    new_master: str,
    new_key_id: str,
) -> EncryptedSecret:
    plaintext = EnvelopeCipher(master_key=old_master, key_id=secret.key_id).decrypt(
        secret
    )
    return EnvelopeCipher(master_key=new_master, key_id=new_key_id).encrypt(plaintext)
