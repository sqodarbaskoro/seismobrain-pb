"""
File: fused_pool.py
Description: Fused pool → rerank set fill after authorization guard (FR-RET-13)
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

from seismobrain_core.fusion import FusedCandidate

RET_FUSED_POOL_K = 120
RERANK_TOP_N = 50


def fill_rerank_set(
    survivors: Sequence[FusedCandidate],
    *,
    rerank_top_n: int = RERANK_TOP_N,
) -> list[FusedCandidate]:
    """Take best guard survivors up to rerank_top_n (order preserved)."""
    if rerank_top_n < 1:
        raise ValueError("rerank_top_n must be >= 1")
    return list(survivors[:rerank_top_n])
