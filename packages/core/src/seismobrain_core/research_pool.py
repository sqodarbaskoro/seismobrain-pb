"""
File: research_pool.py
Description: Merge sub-query retrieval results into global evidence IDs (FR-AGT-02)
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

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SubQueryHit:
    chunk_id: str
    text: str
    score: float
    sub_query_id: str


@dataclass(frozen=True, slots=True)
class PooledEvidence:
    evidence_id: str
    chunk_id: str
    text: str
    score: float
    sub_query_ids: tuple[str, ...]


def merge_research_pool(
    hits: Sequence[SubQueryHit],
    *,
    max_items: int = 16,
) -> list[PooledEvidence]:
    """Dedup by chunk_id; assign global E1..En; keep best score."""
    best: dict[str, SubQueryHit] = {}
    sources: dict[str, list[str]] = {}
    for hit in hits:
        sources.setdefault(hit.chunk_id, []).append(hit.sub_query_id)
        prev = best.get(hit.chunk_id)
        if prev is None or hit.score > prev.score:
            best[hit.chunk_id] = hit
    ranked = sorted(best.values(), key=lambda h: (-h.score, h.chunk_id))[:max_items]
    pooled: list[PooledEvidence] = []
    for i, hit in enumerate(ranked, start=1):
        pooled.append(
            PooledEvidence(
                evidence_id=f"E{i}",
                chunk_id=hit.chunk_id,
                text=hit.text,
                score=hit.score,
                sub_query_ids=tuple(dict.fromkeys(sources[hit.chunk_id])),
            )
        )
    return pooled
