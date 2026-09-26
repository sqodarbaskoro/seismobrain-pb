"""
File: resource_guard.py
Description: Document access store and helpers for preview/download/snapshot (FR-ACL-10)
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


@dataclass
class InMemoryDocumentAccessStore:
    _allowed: set[tuple[str, str]] = field(default_factory=set)
    _evidence_docs: dict[str, str] = field(default_factory=dict)
    _snapshot_docs: dict[str, str] = field(default_factory=dict)

    def grant(self, user_id: str, document_id: str) -> None:
        self._allowed.add((user_id, document_id))

    def revoke(self, user_id: str, document_id: str) -> None:
        self._allowed.discard((user_id, document_id))

    def map_evidence(self, evidence_id: str, document_id: str) -> None:
        self._evidence_docs[evidence_id] = document_id

    def map_snapshot(self, snapshot_id: str, document_id: str) -> None:
        self._snapshot_docs[snapshot_id] = document_id

    def can_read_document(self, user_id: str, document_id: str) -> bool:
        return (user_id, document_id) in self._allowed

    def document_for_evidence(self, evidence_id: str) -> str | None:
        return self._evidence_docs.get(evidence_id)

    def document_for_snapshot(self, snapshot_id: str) -> str | None:
        return self._snapshot_docs.get(snapshot_id)
