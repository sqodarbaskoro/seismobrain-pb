"""
File: test_conflict_surfacing.py
Description: Conflicting evidence with both sides cited (T4.9)
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

from seismobrain_core.conflict_surfacing import ConflictSide, surface_conflict


def test_conflict_fixture_cites_both_sides() -> None:
    statement = surface_conflict(
        [
            ConflictSide(evidence_id="E1", claim="Limit is 6 knots", revision="A"),
            ConflictSide(evidence_id="E2", claim="Limit is 9 knots", revision="B"),
        ]
    )
    assert "E1" in statement.evidence_ids and "E2" in statement.evidence_ids
    assert "[E1]" in statement.text and "[E2]" in statement.text
    assert "Conflicting evidence" in statement.text
    assert "versus" in statement.text
