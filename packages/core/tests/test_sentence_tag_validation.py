"""
File: test_sentence_tag_validation.py
Description: Segment, validate tags, one repair (T3.4)
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

from seismobrain_core.sentence_tag_validation import (
    strip_unknown_tags,
    validate_and_repair,
)


def test_strips_unknown_tags_and_repairs_once() -> None:
    cleaned = strip_unknown_tags("Torque is 40 Nm [E1][E99]", allowed=["E1"])
    assert "[E99]" not in cleaned
    assert "[E1]" in cleaned

    result = validate_and_repair(
        "Torque is 40 Nm.",
        allowed_evidence_ids=["E1"],
        repair=lambda t: t.rstrip(". ") + " [E1]",
    )
    assert result.repaired is True
    assert result.ok
    assert result.sentences[0].evidence_ids == ("E1",)
