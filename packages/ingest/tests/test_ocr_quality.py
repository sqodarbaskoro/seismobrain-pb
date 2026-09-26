"""
File: test_ocr_quality.py
Description: OCR routing with quality metrics (T5.12)
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

from seismobrain_ingest.ocr_quality import score_ocr_page, should_route_to_ocr


def test_ocr_routing_and_quality_flags() -> None:
    assert should_route_to_ocr(digital_text="") is True
    assert should_route_to_ocr(digital_text="x", page_chars=1000) is True
    assert should_route_to_ocr(digital_text="plenty of digital text here") is False
    metrics = score_ocr_page(
        page=1, text="good page text " * 50, confidence=0.9, page_area_chars=200
    )
    assert metrics.extraction_method == "ocr"
    assert metrics.low_quality is False
    bad = score_ocr_page(page=2, text="", confidence=0.2)
    assert bad.low_quality is True
