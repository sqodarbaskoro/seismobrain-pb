"""
File: test_document_tree_persist.py
Description: FR-ING-11 — versioned DocumentTree intermediate persistence
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

from seismobrain_ingest.document_tree import DocumentTree, TreeNode
from seismobrain_ingest.document_tree_store import DocumentTreeStore


def test_rechunk_uses_persisted_tree_without_reparse(tmp_path: Path) -> None:
    store = DocumentTreeStore(tmp_path / "trees")
    original = DocumentTree(
        title="Calibration",
        format="md",
        parser_version="p0-1",
        nodes=[
            TreeNode(type="section", text="Calibration", level=1, heading_path=("Calibration",)),
            TreeNode(type="paragraph", text="Body", heading_path=("Calibration",)),
        ],
    )
    store.put(version_id="ver-1", parser_version="p0-1", tree=original)
    assert store.exists(version_id="ver-1", parser_version="p0-1")
    loaded = store.get(version_id="ver-1", parser_version="p0-1")
    assert loaded.title == "Calibration"
    assert loaded.nodes[0].type == "section"
    assert loaded.nodes[1].text == "Body"
    # Different parser version is a separate artifact (re-parse path).
    assert not store.exists(version_id="ver-1", parser_version="p0-2")
