"""
File: test_degraded_strict.py
Description: Strict mode refuses when verifier/reranker unavailable (T4.26)
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

from seismobrain_core.degraded import DegradedFlags, apply_degraded_strict


def test_strict_refuses_when_verifier_unavailable() -> None:
    result = apply_degraded_strict(flags=DegradedFlags(reranker=True, verifier=False))
    assert result.refused is True
    assert result.refusal_type == "service_unavailable"


def test_strict_refuses_when_reranker_unavailable() -> None:
    result = apply_degraded_strict(flags=DegradedFlags(reranker=False, verifier=True))
    assert result.refused is True


def test_strict_ok_when_services_available() -> None:
    result = apply_degraded_strict(flags=DegradedFlags())
    assert result.refused is False
