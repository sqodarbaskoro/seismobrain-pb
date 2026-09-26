"""
File: test_research_pool.py
Description: Research sub-query merge with global evidence IDs (T5.2)
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

from seismobrain_core.research_pool import SubQueryHit, merge_research_pool


def test_merge_dedups_and_assigns_global_ids() -> None:
    hits = [
        SubQueryHit("c1", "torque 40", 0.9, "sq1"),
        SubQueryHit("c1", "torque 40", 0.8, "sq2"),
        SubQueryHit("c2", "seal procedure", 0.7, "sq2"),
    ]
    pooled = merge_research_pool(hits)
    assert [p.evidence_id for p in pooled] == ["E1", "E2"]
    assert pooled[0].chunk_id == "c1"
    assert pooled[0].score == 0.9
    assert set(pooled[0].sub_query_ids) == {"sq1", "sq2"}
