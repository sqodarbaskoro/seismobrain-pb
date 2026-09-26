"""
File: test_research_latency_nfr.py
Description: Research mode latency budget NFR-PERF-06 (T5.34)
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

import time

from seismobrain_core.research_budgets import BudgetLedger, ResearchBudgets
from seismobrain_core.research_planner import plan_research
from seismobrain_core.research_pool import SubQueryHit, merge_research_pool


def test_research_mode_latency_smoke_fixture() -> None:
    # Offline smoke fixture: planner + pool under local/hosted p95 budgets.
    samples_ms: list[float] = []
    limits = ResearchBudgets(wall_clock_s=60.0)
    for _ in range(20):
        started = time.perf_counter()
        ledger = BudgetLedger(limits=limits)
        frozen = plan_research(
            "compare seal procedure and lockout across plant manuals"
        )
        hits = [
            SubQueryHit(
                chunk_id=f"c{i}",
                text=f"evidence for {sq.text}",
                score=0.9,
                sub_query_id=sq.id,
            )
            for i, sq in enumerate(frozen.plan.sub_queries)
        ]
        pooled = merge_research_pool(hits)
        assert len(pooled) >= 1
        wall_s = time.perf_counter() - started
        assert ledger.charge(retrieval=len(hits), evidence=len(pooled), wall_s=wall_s)
        samples_ms.append(wall_s * 1000.0)
    samples_ms.sort()
    p95_ms = samples_ms[int(0.95 * (len(samples_ms) - 1))]
    # NFR-PERF-06: ≤60s local; ≤30s hosted — smoke fixture is CPU-only.
    assert p95_ms <= 60_000.0
    assert p95_ms <= 30_000.0
