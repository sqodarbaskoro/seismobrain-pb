"""
File: test_numeric_guard.py
Description: Numeric consistency guard (T4.8)
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

from seismobrain_core.numeric_guard import check_numeric_consistency


def test_nine_knots_against_six_knots_is_caught() -> None:
    result = check_numeric_consistency(
        "Normal limit is 9 knots.",
        "Normal limit is 6 knots.",
    )
    assert result.ok is False
    assert any("9" in m for m in result.mismatches)


def test_matching_normalized_units_pass() -> None:
    result = check_numeric_consistency(
        "Speed is 6 kn.",
        "Speed is 6 knots under calm seas.",
    )
    assert result.ok is True
