"""
File: dual_query.py
Description: Retrieve original + rewritten queries and fuse results (FR-QRY-06)
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

from collections.abc import Callable, Sequence
from dataclasses import dataclass

RetrieveFn = Callable[[str], Sequence[tuple[str, float]]]


@dataclass(frozen=True, slots=True)
class FusedHit:
    doc_id: str
    score: float


def _rrf_fuse(
    ranked_lists: Sequence[Sequence[tuple[str, float]]],
    *,
    k: int = 60,
) -> list[FusedHit]:
    scores: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, (doc_id, _raw) in enumerate(ranked, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return [
        FusedHit(doc_id=doc_id, score=score)
        for doc_id, score in sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    ]


def dual_retrieve_and_fuse(
    *,
    original: str,
    rewritten: str,
    retrieve: RetrieveFn,
    rrf_k: int = 60,
) -> list[FusedHit]:
    """Retrieve for original and rewritten (dedupe identical), then RRF-fuse."""
    lists: list[Sequence[tuple[str, float]]] = [retrieve(original)]
    if rewritten != original:
        lists.append(retrieve(rewritten))
    return _rrf_fuse(lists, k=rrf_k)
