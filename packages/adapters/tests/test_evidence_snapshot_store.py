"""
File: test_evidence_snapshot_store.py
Description: EvidenceSnapshotStore inline Starter and encrypted object Team tests
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

from seismobrain_adapters.evidence.inline import InlineEvidenceSnapshotStore
from seismobrain_adapters.evidence.object_encrypted import (
    EncryptedObjectEvidenceSnapshotStore,
)
from seismobrain_adapters.object_store.filesystem import FilesystemObjectStore
from seismobrain_core.ports import EvidenceSnapshotStore

_TEXT = "cited evidence sentence"


def test_inline_evidence_snapshot_store(tmp_path: Path) -> None:
    store: EvidenceSnapshotStore = InlineEvidenceSnapshotStore(tmp_path / "evidence.db")
    uri = store.put(_TEXT)
    assert store.get(uri) == _TEXT


def test_encrypted_object_evidence_snapshot_store(tmp_path: Path) -> None:
    objects = FilesystemObjectStore(tmp_path / "objects")
    key = EncryptedObjectEvidenceSnapshotStore.generate_key()
    store: EvidenceSnapshotStore = EncryptedObjectEvidenceSnapshotStore(
        object_store=objects, encryption_key=key
    )
    uri = store.put(_TEXT)
    assert store.get(uri) == _TEXT
    raw_keys = objects.list_keys("evidence/")
    assert raw_keys
    blob = objects.get(raw_keys[0])
    assert _TEXT.encode() not in blob


def test_encrypted_snapshots_are_content_addressed_immutable(tmp_path: Path) -> None:
    objects = FilesystemObjectStore(tmp_path / "objects")
    key = EncryptedObjectEvidenceSnapshotStore.generate_key()
    store = EncryptedObjectEvidenceSnapshotStore(object_store=objects, encryption_key=key)
    uri1 = store.put(_TEXT)
    before = objects.get(uri1)
    uri2 = store.put(_TEXT)
    assert uri1 == uri2
    assert objects.get(uri1) == before
