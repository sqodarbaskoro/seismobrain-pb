"""
File: test_context_expansion.py
Description: FR-RET-09 — section-bounded expansion context_only
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

from seismobrain_core.context_expansion import expand_within_section


def test_expansion_stays_in_section_and_marks_context_only() -> None:
    spans = expand_within_section(
        anchor_text="Anchor sentence.",
        section_id="s1",
        section_paragraphs=("Anchor sentence.", "Neighbor paragraph."),
    )
    assert all(s.section_id == "s1" for s in spans)
    expanded = [s for s in spans if s.text == "Neighbor paragraph."]
    assert expanded and expanded[0].context_only is True
    assert expanded[0].citable is False


def test_verified_mapping_makes_expanded_citable() -> None:
    spans = expand_within_section(
        anchor_text="Anchor.",
        section_id="s1",
        section_paragraphs=("Anchor.", "Verified neighbor."),
        verified_sentence_map={"claim": "Verified neighbor."},
    )
    neighbor = next(s for s in spans if s.context_only)
    assert neighbor.citable is True
