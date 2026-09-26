"""
File: purge.py
Description: Soft delete and purge job with consistency check (FR-DOC-05)
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

from dataclasses import dataclass, field
from typing import Literal

PurgeMode = Literal["normal", "legal"]


@dataclass(slots=True)
class PurgeResult:
    soft_deleted: bool
    purged: bool
    consistent: bool


@dataclass
class _DocumentRecord:
    file_key: str
    rendition_key: str
    chunk_ids: list[str]
    vector_ids: list[str]
    evidence_snapshot_id: str


@dataclass
class DocumentPurgeStore:
    """In-memory stand-in for metadata + object + vector purge targets."""

    _docs: dict[str, _DocumentRecord] = field(default_factory=dict)
    _files: set[str] = field(default_factory=set)
    _renditions: set[str] = field(default_factory=set)
    _snapshots: set[str] = field(default_factory=set)
    _soft_deleted: set[str] = field(default_factory=set)

    def put_document(
        self,
        *,
        document_id: str,
        file_key: str,
        rendition_key: str,
        chunk_ids: list[str],
        vector_ids: list[str],
        evidence_snapshot_id: str,
    ) -> None:
        self._docs[document_id] = _DocumentRecord(
            file_key=file_key,
            rendition_key=rendition_key,
            chunk_ids=list(chunk_ids),
            vector_ids=list(vector_ids),
            evidence_snapshot_id=evidence_snapshot_id,
        )
        self._files.add(file_key)
        self._renditions.add(rendition_key)
        self._snapshots.add(evidence_snapshot_id)

    def soft_delete(self, document_id: str) -> None:
        if document_id not in self._docs:
            raise KeyError(document_id)
        self._soft_deleted.add(document_id)

    def is_soft_deleted(self, document_id: str) -> bool:
        return document_id in self._soft_deleted

    def purge(self, document_id: str, *, mode: PurgeMode) -> None:
        doc = self._docs[document_id]
        self._files.discard(doc.file_key)
        self._renditions.discard(doc.rendition_key)
        doc.chunk_ids = []
        doc.vector_ids = []
        if mode == "legal":
            self._snapshots.discard(doc.evidence_snapshot_id)

    def has_file(self, key: str) -> bool:
        return key in self._files

    def has_rendition(self, key: str) -> bool:
        return key in self._renditions

    def has_snapshot(self, snapshot_id: str) -> bool:
        return snapshot_id in self._snapshots

    def chunk_ids(self, document_id: str) -> list[str]:
        return list(self._docs[document_id].chunk_ids)

    def vector_ids(self, document_id: str) -> list[str]:
        return list(self._docs[document_id].vector_ids)

    def consistency_ok(self, document_id: str, *, mode: PurgeMode) -> bool:
        doc = self._docs[document_id]
        if self.has_file(doc.file_key) or self.has_rendition(doc.rendition_key):
            return False
        if self.chunk_ids(document_id) or self.vector_ids(document_id):
            return False
        has_snap = self.has_snapshot(doc.evidence_snapshot_id)
        if mode == "legal" and has_snap:
            return False
        if mode == "normal" and not has_snap:
            return False
        return True


def soft_delete_then_purge(
    store: DocumentPurgeStore,
    *,
    document_id: str,
    mode: PurgeMode = "normal",
) -> PurgeResult:
    store.soft_delete(document_id)
    store.purge(document_id, mode=mode)
    return PurgeResult(
        soft_deleted=True,
        purged=True,
        consistent=store.consistency_ok(document_id, mode=mode),
    )
