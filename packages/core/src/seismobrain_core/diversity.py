"""
File: diversity.py
Description: Diversity selection max anchors per section/document with MMR (FR-RET-06)
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
class AnchorCandidate:
    chunk_id: str
    document_id: str
    section_id: str
    score: float
    text: str


def select_diverse_anchors(
    candidates: Sequence[AnchorCandidate],
    *,
    max_per_section: int = 2,
    max_per_document: int = 4,
    final_k: int = 8,
    mmr_lambda: float = 0.7,
) -> list[AnchorCandidate]:
    """Greedy MMR with per-section and per-document caps."""
    remaining = sorted(candidates, key=lambda c: (-c.score, c.chunk_id))
    selected: list[AnchorCandidate] = []
    section_counts: dict[str, int] = {}
    doc_counts: dict[str, int] = {}

    def _overlap(a: str, b: str) -> float:
        ta, tb = set(a.lower().split()), set(b.lower().split())
        if not ta or not tb:
            return 0.0
        return len(ta & tb) / len(ta | tb)

    while remaining and len(selected) < final_k:
        best: AnchorCandidate | None = None
        best_mmr = float("-inf")
        for cand in remaining:
            if section_counts.get(cand.section_id, 0) >= max_per_section:
                continue
            if doc_counts.get(cand.document_id, 0) >= max_per_document:
                continue
            redundancy = 0.0
            if selected:
                redundancy = max(_overlap(cand.text, s.text) for s in selected)
            mmr = mmr_lambda * cand.score - (1.0 - mmr_lambda) * redundancy
            if mmr > best_mmr:
                best_mmr = mmr
                best = cand
        if best is None:
            break
        selected.append(best)
        remaining = [c for c in remaining if c.chunk_id != best.chunk_id]
        section_counts[best.section_id] = section_counts.get(best.section_id, 0) + 1
        doc_counts[best.document_id] = doc_counts.get(best.document_id, 0) + 1
    return selected
