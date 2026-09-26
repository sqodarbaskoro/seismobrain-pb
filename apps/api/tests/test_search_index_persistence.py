"""
File: test_search_index_persistence.py
Description: Retrieval index survives a Starter restart via SQLite write-through
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

from seismobrain_api.search_index import IndexedHit, InMemorySearchIndex


def test_hits_reload_from_db_path_after_restart(tmp_path: Path) -> None:
    db_path = tmp_path / "search_index.db"
    idx = InMemorySearchIndex(db_path=db_path)
    idx.add(
        IndexedHit(
            document_id="d1",
            version_id="d1:v1",
            text="Torque for flange P2/94 is 40 Nm.",
            collection_id="manuals",
            score=1.0,
            metadata={"chunk_id": "d1:chunk-1", "title": "pump_manual"},
        )
    )

    restarted = InMemorySearchIndex(db_path=db_path)
    hits = restarted.query(text="flange torque", collection_ids=["manuals"])
    assert hits
    assert hits[0].document_id == "d1"
    assert hits[0].metadata["chunk_id"] == "d1:chunk-1"


def test_without_db_path_stays_purely_in_memory(tmp_path: Path) -> None:
    idx = InMemorySearchIndex()
    idx.add(
        IndexedHit(
            document_id="d1",
            version_id="d1:v1",
            text="ephemeral",
            collection_id="manuals",
            score=1.0,
        )
    )
    assert idx.db_path is None
    assert not (tmp_path / "search_index.db").exists()
