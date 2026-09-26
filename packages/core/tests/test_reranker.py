"""
File: test_reranker.py
Description: FR-RET-03 — cross-encoder reranking via models service
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

from seismobrain_adapters.models.in_process import InProcessModelGateway
from seismobrain_core.reranker import RerankCandidate, rerank_candidates


def test_reranker_reorders_and_reports_uplift() -> None:
    gateway = InProcessModelGateway()
    candidates = [
        RerankCandidate("a", "unrelated text about weather", 1.0),
        RerankCandidate("b", "pump seal procedure pump seal", 0.5),
        RerankCandidate("c", "other notes", 0.4),
    ]
    result = rerank_candidates(
        query="pump seal",
        candidates=candidates,
        gateway=gateway,
    )
    assert result.ordered[0].doc_id == "b"
    assert result.uplift > 0
