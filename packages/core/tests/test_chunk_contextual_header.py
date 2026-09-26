"""
File: test_chunk_contextual_header.py
Description: FR-CHK-05 — contextual header separate from evidence text
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

from seismobrain_core.chunking import SectionInput, build_contextual_header, chunk_document


def test_contextual_header_not_in_evidence_text() -> None:
    header = build_contextual_header(
        document_title="Manual",
        revision="3",
        heading_path=("Setup", "Power"),
    )
    assert "Document: Manual" in header
    assert "Revision: 3" in header
    assert "Section: Setup / Power" in header

    result = chunk_document(
        [
            SectionInput(
                section_id="s1",
                heading_path=("Setup", "Power"),
                paragraphs=("Connect the cable.",),
            )
        ],
        document_title="Manual",
        revision="3",
    )
    chunk = result.children[0]
    assert chunk.contextual_header == header
    assert "Document: Manual" not in chunk.text
    assert chunk.text == "Connect the cable."
