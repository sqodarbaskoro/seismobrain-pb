"""
File: test_verifier_set_size.py
Description: Verifier evaluation set ≥300 class-balanced (T3.24)
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

from collections import Counter

from seismobrain_eval.verifier_set import build_verifier_set


def test_verifier_set_size_and_balance() -> None:
    pairs = build_verifier_set(size=300)
    assert len(pairs) >= 300
    counts = Counter(p.label for p in pairs)
    assert set(counts) >= {"supported", "partial", "unsupported", "no_citation"}
    assert min(counts.values()) >= 70
    assert any(p.tag == "near_miss_numeric" for p in pairs)
