"""
File: test_evidence_tag_lint.py
Description: Factual sentences require E-tags; ban filenames/pages (T3.3)
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

from seismobrain_core.evidence_tag_lint import lint_evidence_tags


def test_lint_accepts_terminal_etags() -> None:
    result = lint_evidence_tags("Torque is 40 Nm [E1]")
    assert result.ok


def test_lint_rejects_filename_page_section() -> None:
    bad = lint_evidence_tags("See manual.pdf page 12 section 4.2 for torque [E1]")
    assert not bad.ok
    assert "filename_citation" in bad.errors
    assert "page_citation" in bad.errors
    assert "section_citation" in bad.errors


def test_lint_accepts_insufficient_evidence() -> None:
    assert lint_evidence_tags("INSUFFICIENT_EVIDENCE").ok
