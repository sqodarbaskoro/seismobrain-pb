"""
File: test_soft_delete_purge.py
Description: FR-DOC-05 — soft delete then purge with consistency check
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

from seismobrain_ingest.purge import DocumentPurgeStore, soft_delete_then_purge


def test_soft_delete_then_purge_removes_artifacts_keeps_snapshot_on_normal_delete() -> None:
    store = DocumentPurgeStore()
    store.put_document(
        document_id="doc-1",
        file_key="files/doc-1.pdf",
        rendition_key="renditions/doc-1.pdf",
        chunk_ids=["c1", "c2"],
        vector_ids=["v1", "v2"],
        evidence_snapshot_id="snap-1",
    )
    result = soft_delete_then_purge(store, document_id="doc-1", mode="normal")
    assert result.soft_deleted is True
    assert result.purged is True
    assert result.consistent is True
    assert store.is_soft_deleted("doc-1")
    assert not store.has_file("files/doc-1.pdf")
    assert not store.has_rendition("renditions/doc-1.pdf")
    assert store.chunk_ids("doc-1") == []
    assert store.vector_ids("doc-1") == []
    # Normal delete retains evidence snapshots (§9.3).
    assert store.has_snapshot("snap-1")


def test_legal_purge_destroys_evidence_snapshot() -> None:
    store = DocumentPurgeStore()
    store.put_document(
        document_id="doc-2",
        file_key="files/doc-2.pdf",
        rendition_key="renditions/doc-2.pdf",
        chunk_ids=["c9"],
        vector_ids=["v9"],
        evidence_snapshot_id="snap-2",
    )
    result = soft_delete_then_purge(store, document_id="doc-2", mode="legal")
    assert result.consistent is True
    assert not store.has_snapshot("snap-2")
