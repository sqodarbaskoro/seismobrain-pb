"""
File: object_encrypted.py
Description: Encrypted compressed object-store EvidenceSnapshotStore for Team
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
import zlib

from cryptography.fernet import Fernet

from seismobrain_core.ports import ObjectStore


class EncryptedObjectEvidenceSnapshotStore:
    """Team EvidenceSnapshotStore: immutable gzip+Fernet blobs in ObjectStore."""

    def __init__(self, *, object_store: ObjectStore, encryption_key: bytes) -> None:
        self._store = object_store
        self._fernet = Fernet(encryption_key)

    @staticmethod
    def generate_key() -> bytes:
        return Fernet.generate_key()

    def put(self, text: str) -> str:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        uri = f"evidence/{digest}"
        if self._store.exists(uri):
            return uri
        compressed = zlib.compress(text.encode("utf-8"), level=9)
        encrypted = self._fernet.encrypt(compressed)
        self._store.put(uri, encrypted)
        return uri

    def get(self, uri: str) -> str:
        encrypted = self._store.get(uri)
        compressed = self._fernet.decrypt(encrypted)
        return zlib.decompress(compressed).decode("utf-8")
