"""
File: test_rerank_latency_nfr.py
Description: Rerank latency budget NFR-PERF-02 (T3.34)
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

from seismobrain_adapters.models.in_process import InProcessModelGateway


def test_rerank_30_candidates_cpu_budget() -> None:
    gateway = InProcessModelGateway()
    docs = [f"document about torque and flanges number {i}" for i in range(30)]
    samples: list[float] = []
    for _ in range(20):
        started = time.perf_counter()
        gateway.rerank("torque flange", docs, model_id="cpu-rerank")
        samples.append((time.perf_counter() - started) * 1000.0)
    samples.sort()
    p95 = samples[int(0.95 * (len(samples) - 1))]
    assert p95 <= 2000.0
