"""
File: test_rewrite_identifier_guard.py
Description: FR-QRY-05 — rewrite guard preserves identifiers 100%
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

from seismobrain_core.identifiers import detect_identifiers
from seismobrain_core.query_rewrite import guarded_rewrite


def test_rewrite_dropping_identifier_is_discarded() -> None:
    original = "Clear error E-404 on well-alpha-12"
    history = ("Previous turn about the pump.",)
    result = guarded_rewrite(
        original,
        history=history,
        rewriter=lambda q, _h: "Clear the error on the unit",
    )
    assert result.rewritten is False
    assert result.query == original
    assert detect_identifiers(original) == detect_identifiers(result.query)


def test_rewrite_preserving_identifiers_is_kept() -> None:
    original = "Clear error E-404 on well-alpha-12"
    result = guarded_rewrite(
        original,
        history=("Discussing pumps.",),
        rewriter=lambda q, _h: "How do I clear error E-404 on well-alpha-12?",
    )
    assert result.rewritten is True
    for token in detect_identifiers(original):
        assert token in result.query


def test_identifier_preservation_is_complete_on_fixture_set() -> None:
    cases = (
        ("Torque P2/94", "What is torque for P2/94?"),
        ("Host 10.0.0.15 status", "Status of host 10.0.0.15"),
        ("HSE lockout", "HSE lockout steps"),
    )
    for original, good_rewrite in cases:
        result = guarded_rewrite(
            original,
            history=("ctx",),
            rewriter=lambda _q, _h, r=good_rewrite: r,
        )
        assert result.rewritten is True
        for token in detect_identifiers(original):
            assert token in result.query
