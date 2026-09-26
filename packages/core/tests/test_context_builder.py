"""
File: test_context_builder.py
Description: FR-RET-08 — context builder E1..En and token budget
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

from seismobrain_core.context_builder import EvidenceItem, build_context


def test_assigns_evidence_ids_by_relevance_and_drops_overflow() -> None:
    items = [
        EvidenceItem("c1", "one two three four five", 0.5),
        EvidenceItem("c2", "alpha beta", 0.9),
        EvidenceItem("c3", "gamma delta epsilon zeta", 0.8),
    ]
    ctx = build_context(items, max_tokens=5)
    labels = [label for label, _ in ctx.blocks]
    assert labels[0] == "E1"
    assert ctx.blocks[0][1].chunk_id == "c2"
    assert ctx.token_count <= 5
    assert ctx.dropped
