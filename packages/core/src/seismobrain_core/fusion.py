"""
File: fusion.py
Description: Reference weighted RRF fusion for parity and fallback (FR-RET-02)
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

from collections.abc import Mapping, Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FusedCandidate:
    doc_id: str
    score: float


def weighted_rrf(
    arms: Mapping[str, Sequence[tuple[str, float]]],
    *,
    weights: Mapping[str, float],
    k: int = 60,
) -> list[FusedCandidate]:
    """Weighted reciprocal rank fusion; rankings are deterministic on fixtures."""
    if k < 1:
        raise ValueError("k must be >= 1")
    scores: dict[str, float] = {}
    for arm_name, ranked in arms.items():
        weight = float(weights.get(arm_name, 1.0))
        for rank, (doc_id, _raw) in enumerate(ranked, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + weight * (1.0 / (k + rank))
    return [
        FusedCandidate(doc_id=doc_id, score=score)
        for doc_id, score in sorted(
            scores.items(), key=lambda item: (-item[1], item[0])
        )
    ]
