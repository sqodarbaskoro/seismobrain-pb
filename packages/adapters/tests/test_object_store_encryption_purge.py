"""
File: test_object_store_encryption_purge.py
Description: SEC-28 — snapshot object storage SSE and purge all versions
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

from pathlib import Path

from cryptography.fernet import Fernet

from seismobrain_adapters.object_store.encrypted import ServerSideEncryptedObjectStore
from seismobrain_adapters.object_store.filesystem import FilesystemObjectStore


def test_server_side_encryption_and_purge_all_versions(tmp_path: Path) -> None:
    key = Fernet.generate_key()
    inner = FilesystemObjectStore(tmp_path / "objects")
    store = ServerSideEncryptedObjectStore(inner, encryption_key=key)
    assert store.server_side_encryption is True

    store.put("snapshots/msg-1", b"evidence-v1")
    store.put("snapshots/msg-1", b"evidence-v2")
    assert store.get("snapshots/msg-1") == b"evidence-v2"
    versions = store.list_versions("snapshots/msg-1")
    assert len(versions) == 2
    # Ciphertext at rest is not plaintext.
    for version_key in versions:
        raw = inner.get(version_key)
        assert b"evidence" not in raw

    store.purge_all_versions("snapshots/msg-1")
    assert store.exists("snapshots/msg-1") is False
    assert store.list_versions("snapshots/msg-1") == []
    for version_key in versions:
        assert inner.exists(version_key) is False
