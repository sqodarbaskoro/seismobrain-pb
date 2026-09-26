"""
File: test_retrieval_latency_nfr.py
Description: Retrieval latency budget NFR-PERF-01 (T2.31)
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

from seismobrain_core.fusion import weighted_rrf
from seismobrain_eval.runner import measure_retrieval_latency_ms


def _smoke_retrieval() -> list[str]:
    dense = [(f"d{i}", 1.0 / (i + 1)) for i in range(30)]
    bm25 = [(f"d{i}", 1.0 / (i + 2)) for i in range(30)]
    ident = [("d0", 1.0), ("d1", 0.5)]
    fused = weighted_rrf(
        {"dense": dense, "bm25_text": bm25, "ident": ident},
        weights={"dense": 1.0, "bm25_text": 1.0, "ident": 1.2},
    )
    return [h.doc_id for h in fused]


def test_retrieval_latency_p95_within_starter_budget() -> None:
    # Starter ≤800 ms; Team ≤300 ms. Offline fusion smoke must clear Team.
    p95 = measure_retrieval_latency_ms(_smoke_retrieval, iterations=30)
    assert p95 <= 300.0, f"p95={p95} ms exceeds Team budget"
