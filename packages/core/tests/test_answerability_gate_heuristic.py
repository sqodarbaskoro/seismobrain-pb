"""
File: test_answerability_gate_heuristic.py
Description: FR-RET-05 — heuristic query-level answerability gate
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-17
Version: 0.2.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from seismobrain_core.answerability import (
    EvidenceSnippet,
    heuristic_answerability,
)


def test_overlapping_evidence_is_answerable() -> None:
    decision = heuristic_answerability(
        "pump seal procedure",
        [EvidenceSnippet("The pump seal procedure requires isolation.", 0.8)],
    )
    assert decision.answerable is True


def test_unrelated_evidence_not_answerable() -> None:
    decision = heuristic_answerability(
        "pump seal procedure",
        [EvidenceSnippet("The cafeteria menu changes weekly.", 0.9)],
    )
    assert decision.answerable is False
    assert decision.reason == "insufficient_evidence"


def test_empty_evidence_refuses() -> None:
    decision = heuristic_answerability("anything", [])
    assert decision.answerable is False
    assert decision.reason == "no_evidence"


def test_inventory_question_with_scoped_evidence_is_answerable() -> None:
    decision = heuristic_answerability(
        "What's in my documents?",
        [EvidenceSnippet("Torque for flange P2/94 is 40 Nm.", 1.0)],
    )
    assert decision.answerable is True
    assert decision.reason == "scoped_inventory"
