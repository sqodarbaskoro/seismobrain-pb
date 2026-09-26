"""
File: test_search_index_fallback.py
Description: Keyword search must still return scoped docs when the query has no token hits
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-17
Modified: 2026-09-17
Version: 0.1.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from seismobrain_api.search_index import IndexedHit, InMemorySearchIndex


def _index() -> InMemorySearchIndex:
    idx = InMemorySearchIndex()
    idx.add(
        IndexedHit(
            document_id="d1",
            version_id="d1:v1",
            text="Torque for flange P2/94 is 40 Nm.",
            collection_id="manuals",
            score=1.0,
            metadata={"title": "pump_manual"},
        )
    )
    idx.add(
        IndexedHit(
            document_id="d2",
            version_id="d2:v1",
            text="Always wear PPE when servicing pumps.",
            collection_id="manuals",
            score=0.8,
            metadata={"title": "safety_note"},
        )
    )
    idx.add(
        IndexedHit(
            document_id="d3",
            version_id="d3:v1",
            text="Secret other collection content.",
            collection_id="other",
            score=0.9,
            metadata={"title": "other"},
        )
    )
    return idx


def test_keyword_hit_still_preferred() -> None:
    hits = _index().query(text="flange torque", collection_ids=["manuals"])
    assert hits
    assert hits[0].document_id == "d1"


def test_punctuation_does_not_block_match() -> None:
    hits = _index().query(text="pumps?", collection_ids=["manuals"])
    assert any(h.document_id == "d2" for h in hits)


def test_generic_question_falls_back_to_scoped_docs() -> None:
    hits = _index().query(text="What's in my documents?", collection_ids=["manuals"])
    assert {h.document_id for h in hits} == {"d1", "d2"}


def test_fallback_respects_collection_scope() -> None:
    hits = _index().query(text="What's in my documents?", collection_ids=["other"])
    assert [h.document_id for h in hits] == ["d3"]
