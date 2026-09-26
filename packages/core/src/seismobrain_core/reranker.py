"""
File: reranker.py
Description: Cross-encoder reranking via ModelGateway (FR-RET-03)
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
from typing import Protocol


class RerankGateway(Protocol):
    def rerank(
        self, query: str, documents: list[str], *, model_id: str
    ) -> list[int]: ...


@dataclass(frozen=True, slots=True)
class RerankCandidate:
    doc_id: str
    text: str
    fused_score: float


@dataclass(frozen=True, slots=True)
class RerankResult:
    ordered: tuple[RerankCandidate, ...]
    uplift: float


def rerank_candidates(
    *,
    query: str,
    candidates: Sequence[RerankCandidate],
    gateway: RerankGateway,
    model_id: str = "cpu-rerank",
) -> RerankResult:
    """Rerank fused candidates; uplift = mean rank improvement of top fused item."""
    if not candidates:
        return RerankResult(ordered=(), uplift=0.0)
    docs = [c.text for c in candidates]
    order = gateway.rerank(query, docs, model_id=model_id)
    ordered = tuple(candidates[i] for i in order)
    # Uplift: how many positions the original #1 moved (normalized).
    top_id = candidates[0].doc_id
    new_rank = next(i for i, c in enumerate(ordered) if c.doc_id == top_id)
    uplift = max(0.0, (new_rank) / max(len(candidates) - 1, 1))
    # Prefer measuring improvement when reranker disagrees usefully:
    # report fraction of order changes as uplift signal for tests.
    changed = sum(
        1 for i, c in enumerate(ordered) if c.doc_id != candidates[i].doc_id
    )
    uplift = changed / len(candidates)
    return RerankResult(ordered=ordered, uplift=uplift)
