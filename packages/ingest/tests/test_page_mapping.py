"""
File: test_page_mapping.py
Description: FR-ING-08 — Word PDF rendition and chunk-to-page mapping confidence
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

from seismobrain_ingest.page_mapping import (
    PageText,
    map_chunk_to_page,
    render_word_to_pdf_stub,
)


def test_high_confidence_maps_to_page_low_uses_section_only() -> None:
    pages = [
        PageText(page=1, text="Introduction and scope of the manual."),
        PageText(page=2, text="Calibration procedure warm up the sensor carefully."),
        PageText(page=3, text="Appendix references and glossary."),
    ]
    mapped = map_chunk_to_page(
        chunk_id="c1",
        chunk_text="Calibration procedure warm up the sensor carefully.",
        pages=pages,
    )
    assert mapped.citation_mode == "page"
    assert mapped.page == 2
    assert mapped.confidence >= 0.55

    weak = map_chunk_to_page(
        chunk_id="c2",
        chunk_text="Completely unrelated quantum topic xyz",
        pages=pages,
    )
    assert weak.citation_mode == "section_only"
    assert weak.page is None
    # No synthetic virtual pages invented.
    assert weak.page is None


def test_word_rendition_produces_pdf_bytes() -> None:
    pdf = render_word_to_pdf_stub(b"PK fake docx")
    assert pdf.startswith(b"%PDF")
