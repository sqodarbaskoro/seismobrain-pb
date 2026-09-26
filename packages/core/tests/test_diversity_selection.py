"""
File: test_diversity_selection.py
Description: FR-RET-06 — max anchors per section/document with MMR
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

from seismobrain_core.diversity import AnchorCandidate, select_diverse_anchors


def test_caps_per_section_and_document() -> None:
    cands = [
        AnchorCandidate(f"c{i}", "doc1", "sec1", 1.0 - i * 0.01, f"alpha text {i}")
        for i in range(6)
    ] + [
        AnchorCandidate(f"d{i}", "doc1", "sec2", 0.5 - i * 0.01, f"beta text {i}")
        for i in range(6)
    ]
    selected = select_diverse_anchors(
        cands, max_per_section=2, max_per_document=4, final_k=8
    )
    assert len(selected) == 4  # doc cap
    assert sum(1 for s in selected if s.section_id == "sec1") <= 2
    assert sum(1 for s in selected if s.document_id == "doc1") <= 4
