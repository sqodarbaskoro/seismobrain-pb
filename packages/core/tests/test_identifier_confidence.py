"""
File: test_identifier_confidence.py
Description: Identifier confidence classes and ident arm weights (T4.12)
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

from seismobrain_core.identifier_confidence import (
    IdentifierConfidence,
    analyze_identifiers,
    over_detection_rate,
)


def test_confidence_classes_drive_ident_weight() -> None:
    high = analyze_identifiers(
        "Check flange FL-204",
        glossary=("FL-204",),
    )
    assert high.highest is IdentifierConfidence.HIGH
    assert high.ident_weight == 1.5
    assert high.skip_ident_arm is False

    medium = analyze_identifiers("Error E-42 on panel")
    assert medium.highest is IdentifierConfidence.MEDIUM
    assert medium.ident_weight == 1.2

    low = analyze_identifiers("What about HVAC?")
    assert low.highest is IdentifierConfidence.LOW
    assert low.ident_weight == 1.0
    assert low.skip_ident_arm is True


def test_excludes_dates_versions_paths_and_measures_over_detection() -> None:
    result = analyze_identifiers("See 2024-01-01 v1.2.3 /tmp/a.pdf section 3.1")
    assert result.identifiers == ()
    rate = over_detection_rate(["HVAC", "noise"], ["HVAC"])
    assert rate == 0.5
