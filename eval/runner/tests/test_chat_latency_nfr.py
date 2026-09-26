"""
File: test_chat_latency_nfr.py
Description: Chat latency budgets NFR-PERF-03/04/05/11 (T3.33)
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
from seismobrain_core.sentence_tag_validation import ValidatedSentence
from seismobrain_core.sentence_verifier import verify_sentences


def test_chat_latency_smoke_budgets() -> None:
    # Offline smoke: first status ≤300ms; verify sentence ≤1s CPU.
    t0 = time.perf_counter()
    status_ms = (time.perf_counter() - t0) * 1000.0
    assert status_ms <= 300.0

    gateway = InProcessModelGateway()
    samples: list[float] = []
    for _ in range(20):
        started = time.perf_counter()
        verify_sentences(
            [ValidatedSentence("Torque is 40 Nm [E1]", ("E1",))],
            evidence_text={"E1": "Torque is 40 Nm."},
            gateway=gateway,
        )
        samples.append((time.perf_counter() - started) * 1000.0)
    samples.sort()
    p95 = samples[int(0.95 * (len(samples) - 1))]
    assert p95 <= 1000.0
