"""
File: test_collection_access.py
Description: Document catalog survives a Starter restart via SQLite write-through
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-18
Modified: 2026-09-18
Version: 0.1.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from pathlib import Path

from seismobrain_api.collection_access import InMemoryCollectionAccessStore


def test_documents_reload_from_db_path_after_restart(tmp_path: Path) -> None:
    db_path = tmp_path / "documents.db"
    store = InMemoryCollectionAccessStore(db_path=db_path)
    store.add_document(
        document_id="d1",
        collection_id="col1",
        title="Flange torque spec",
        doc_type="pdf",
        tags=("mechanical",),
        source_path="flange.pdf",
        object_key="collections/col1/documents/d1/flange.pdf",
    )

    restarted = InMemoryCollectionAccessStore(db_path=db_path)
    doc = restarted.get_document("d1")
    assert doc is not None
    assert doc["title"] == "Flange torque spec"
    assert doc["collection_id"] == "col1"
    assert doc["object_key"] == "collections/col1/documents/d1/flange.pdf"


def test_document_edits_persist_across_restart(tmp_path: Path) -> None:
    db_path = tmp_path / "documents.db"
    store = InMemoryCollectionAccessStore(db_path=db_path)
    store.add_document(document_id="d1", collection_id="col1", title="Note")
    store.move_document("d1", "col2")
    store.retag_document("d1", ["reviewed"])
    store.delete_document("d1")

    restarted = InMemoryCollectionAccessStore(db_path=db_path)
    doc = restarted.get_document("d1")
    assert doc is not None
    assert doc["collection_id"] == "col2"
    assert doc["tag"] == "reviewed"
    assert doc["deleted"] is True


def test_without_db_path_stays_purely_in_memory(tmp_path: Path) -> None:
    store = InMemoryCollectionAccessStore()
    store.add_document(document_id="d1", collection_id="col1", title="Note")
    assert store.db_path is None
    assert not (tmp_path / "documents.db").exists()
