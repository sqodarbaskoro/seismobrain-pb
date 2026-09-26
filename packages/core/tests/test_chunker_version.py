"""
File: test_chunker_version.py
Description: FR-CHK-07 — chunker_version recorded on chunks
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

from seismobrain_core.chunking import CHUNKER_VERSION, SectionInput, chunk_document


def test_chunker_version_on_all_chunks() -> None:
    result = chunk_document(
        [SectionInput(section_id="s1", heading_path=("A",), paragraphs=("Hello world.",))],
        document_title="Doc",
    )
    assert CHUNKER_VERSION
    assert all(c.chunker_version == CHUNKER_VERSION for c in result.children)
    assert all(c.chunker_version == CHUNKER_VERSION for c in result.parents)
