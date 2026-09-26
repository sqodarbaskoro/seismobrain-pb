"""
File: test_document_text.py
Description: extract_document_sections groups paragraphs by detected heading (FR-CHK-*)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-18
Modified: 2026-09-18
Version: 0.1.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from seismobrain_api.document_text import extract_document_sections


def test_txt_fallback_has_no_heading_path() -> None:
    sections = extract_document_sections("note.txt", b"Plain text body without headings.")
    assert sections == [((), ["Plain text body without headings."])]


def test_markdown_headings_group_paragraphs() -> None:
    data = b"# Intro\n\nFirst paragraph.\n\n## Details\n\nSecond paragraph.\n"
    sections = extract_document_sections("note.md", data)
    heading_paths = [heading for heading, _ in sections]
    assert ("Intro",) in heading_paths
    assert ("Intro", "Details") in heading_paths
