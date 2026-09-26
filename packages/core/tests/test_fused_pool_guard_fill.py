"""
File: test_fused_pool_guard_fill.py
Description: FR-RET-13 — fused pool fills rerank set after guard drops
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

from seismobrain_core.fused_pool import RERANK_TOP_N, RET_FUSED_POOL_K, fill_rerank_set
from seismobrain_core.fusion import FusedCandidate


def test_fused_pool_larger_than_rerank_set() -> None:
    assert RET_FUSED_POOL_K > RERANK_TOP_N
    assert RET_FUSED_POOL_K == 120
    assert RERANK_TOP_N == 50


def test_guard_drops_filled_from_survivors_recall_stable() -> None:
    fused = [
        FusedCandidate(doc_id=f"d{i}", score=float(RET_FUSED_POOL_K - i))
        for i in range(RET_FUSED_POOL_K)
    ]
    # Revoke 30% spread across the pool (including top ranks).
    revoked = {c.doc_id for i, c in enumerate(fused) if i % 10 < 3}
    assert abs(len(revoked) / len(fused) - 0.30) < 0.01

    survivors = [c for c in fused if c.doc_id not in revoked]

    # Naive: filter after truncating to rerank_top_n → undersized set.
    naive = [c for c in fused[:RERANK_TOP_N] if c.doc_id not in revoked]
    assert len(naive) < RERANK_TOP_N

    filled = fill_rerank_set(survivors, rerank_top_n=RERANK_TOP_N)
    assert len(filled) == RERANK_TOP_N
    assert all(c.doc_id not in revoked for c in filled)

    relevant = {c.doc_id for c in fused[:RERANK_TOP_N]}
    naive_hits = sum(1 for c in naive if c.doc_id in relevant)
    filled_hits = sum(1 for c in filled if c.doc_id in relevant)
    assert filled_hits >= naive_hits
