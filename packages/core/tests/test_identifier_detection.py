"""
File: test_identifier_detection.py
Description: FR-QRY-03 — identifier detection with configurable patterns
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

from seismobrain_core.identifiers import (
    IdentifierDetector,
    detect_identifiers,
    preserve_identifiers,
)


def test_default_patterns_detect_common_ids() -> None:
    text = "Replace gasket P2/94 and clear E-404 on well-alpha-12 near 10.0.0.15"
    found = detect_identifiers(text)
    assert "P2/94" in found
    assert "E-404" in found or "E404" in found or any("404" in x for x in found)
    assert "well-alpha-12" in found
    assert "10.0.0.15" in found


def test_identifiers_preserved_verbatim() -> None:
    original = "Torque for flange P2/94 per API"
    found = detect_identifiers(original)
    assert "P2/94" in found
    rewritten = "What is the torque specification for the flange according to the standard?"
    guarded = preserve_identifiers(original, rewritten, found)
    # Dropped identifier → discard rewrite (return original).
    assert guarded == original


def test_rewrite_kept_when_all_identifiers_preserved() -> None:
    original = "Torque for flange P2/94"
    found = detect_identifiers(original)
    rewritten = "What is the torque for flange P2/94?"
    assert preserve_identifiers(original, rewritten, found) == rewritten


def test_configurable_extra_pattern() -> None:
    detector = IdentifierDetector(extra_patterns=(r"\bSN-\d{4}\b",))
    found = detector.detect("Serial SN-1234 failed")
    assert "SN-1234" in found
