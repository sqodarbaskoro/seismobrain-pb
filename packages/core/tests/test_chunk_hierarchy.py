"""
File: test_chunk_hierarchy.py
Description: FR-CHK-02 — child chunks and capped parent sections
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

from seismobrain_core.chunking import SectionInput, chunk_document, whitespace_token_count


def test_child_and_capped_parent_sections() -> None:
    section = SectionInput(
        section_id="s1",
        heading_path=("Overview",),
        paragraphs=tuple(f"Sentence number {i} is here." for i in range(1, 40)),
    )
    result = chunk_document(
        [section],
        document_title="Manual",
        child_max_tokens=20,
        parent_max_tokens=40,
    )
    assert result.children
    assert len(result.parents) == 1
    parent = result.parents[0]
    assert parent.chunk_type == "parent_section"
    assert whitespace_token_count(parent.text) <= 40
    assert all(c.parent_section_id == parent.chunk_id for c in result.children)
