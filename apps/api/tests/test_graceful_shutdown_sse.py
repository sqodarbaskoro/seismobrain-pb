"""
File: test_graceful_shutdown_sse.py
Description: API drains SSE streams on graceful shutdown (T3.30)
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

from seismobrain_api.sse_lifecycle import SseDrainController


def test_sse_drain_budget_30_seconds() -> None:
    ctrl = SseDrainController(drain_seconds=30)
    assert ctrl.drain_seconds == 30
    handle = ctrl.register("stream-1")
    assert ctrl.active_count == 1
    ctrl.begin_shutdown()
    assert ctrl.draining is True
    assert ctrl.should_accept_new is False
    handle.close()
    assert ctrl.active_count == 0
    assert ctrl.wait_until_drained(timeout_s=0.1) is True
