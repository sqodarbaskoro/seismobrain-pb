"""
File: encrypted.py
Description: Server-side encrypted ObjectStore wrapper with versioned purge (SEC-28)
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

from cryptography.fernet import Fernet

from seismobrain_core.ports import ObjectStore


class ServerSideEncryptedObjectStore:
    """ObjectStore that encrypts payloads at rest and can purge all key versions."""

    def __init__(self, inner: ObjectStore, *, encryption_key: bytes) -> None:
        self._inner = inner
        self._fernet = Fernet(encryption_key)
        self.server_side_encryption = True
        # Logical key -> list of versioned physical keys (newest last).
        self._versions: dict[str, list[str]] = {}

    def put(self, key: str, data: bytes) -> None:
        encrypted = self._fernet.encrypt(data)
        versions = self._versions.setdefault(key, [])
        version_key = f"{key}#v{len(versions) + 1}"
        versions.append(version_key)
        self._inner.put(version_key, encrypted)
        # Current pointer for get/exists.
        self._inner.put(key, version_key.encode("utf-8"))

    def get(self, key: str) -> bytes:
        pointer = self._inner.get(key).decode("utf-8")
        encrypted = self._inner.get(pointer)
        return self._fernet.decrypt(encrypted)

    def delete(self, key: str) -> None:
        self.purge_all_versions(key)

    def exists(self, key: str) -> bool:
        return self._inner.exists(key)

    def list_keys(self, prefix: str = "") -> list[str]:
        return [
            k
            for k in self._versions
            if k.startswith(prefix) and self._inner.exists(k)
        ]

    def list_versions(self, key: str) -> list[str]:
        return list(self._versions.get(key, []))

    def purge_all_versions(self, key: str) -> None:
        for version_key in self._versions.get(key, []):
            self._inner.delete(version_key)
        self._inner.delete(key)
        self._versions.pop(key, None)
