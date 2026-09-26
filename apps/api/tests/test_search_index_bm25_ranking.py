"""
File: test_search_index_bm25_ranking.py
Description: Regression for Starter retrieval miss — real BM25 scoring must rank a
    high-overlap chunk above weak single-token matches, not just "any token OR match"
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-18
Modified: 2026-09-19
Version: 0.2.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from seismobrain_api.search_index import IndexedHit, InMemorySearchIndex

_NEEDLE_TEXT = (
    "The batch sequence number reported by OpsConsole RT is computed in the "
    "Sequence Controller from the anchor event, using the path distance from "
    "the start of line (DA) in Distance mode and elapsed time in Time mode."
)

_QUESTION = (
    "How does OpsConsole RT compute the batch sequence number in the Sequence Controller?"
)


def _index_with_distractors() -> InMemorySearchIndex:
    idx = InMemorySearchIndex()
    # Real ingestion always scores every chunk 1.0 (see starter_ingest.py); many weak
    # distractors match on a single shared token ("opsconsole") before the real answer.
    for i in range(50):
        idx.add(
            IndexedHit(
                document_id=f"distractor-{i}",
                version_id=f"distractor-{i}:v1",
                text=(
                    f"OpsConsole node deployment note {i}: "
                    "radio beacon height reference."
                ),
                collection_id="manuals",
                score=1.0,
                metadata={"title": "Ch12_Hardware"},
            )
        )
    idx.add(
        IndexedHit(
            document_id="ch03-answer",
            version_id="ch03-answer:v1",
            text=_NEEDLE_TEXT,
            collection_id="manuals",
            score=1.0,
            metadata={"title": "Ch03_Data_Prep"},
        )
    )
    return idx


def test_high_overlap_chunk_outranks_weak_single_token_matches() -> None:
    hits = _index_with_distractors().query(text=_QUESTION, collection_ids=["manuals"])
    assert hits[0].document_id == "ch03-answer"


def test_high_overlap_chunk_is_within_top_20() -> None:
    hits = _index_with_distractors().query(text=_QUESTION, collection_ids=["manuals"])
    top20_ids = {h.document_id for h in hits[:20]}
    assert "ch03-answer" in top20_ids
