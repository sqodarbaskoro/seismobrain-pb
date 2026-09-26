"""
File: ocr_quality.py
Description: OCR routing and quality metrics (FR-PARSE-04, FR-ING-07)
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

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PageOcrMetrics:
    page: int
    confidence: float
    invalid_char_ratio: float
    text_density: float
    low_quality: bool
    extraction_method: str


def should_route_to_ocr(*, digital_text: str, page_chars: int = 0) -> bool:
    """Route scanned or sparse pages to OCR."""
    stripped = digital_text.strip()
    if not stripped:
        return True
    if page_chars > 0 and len(stripped) / page_chars < 0.02:
        return True
    return False


def score_ocr_page(
    *,
    page: int,
    text: str,
    confidence: float,
    page_area_chars: int = 2000,
) -> PageOcrMetrics:
    if not text:
        invalid = 1.0
        density = 0.0
    else:
        invalid = sum(1 for c in text if ord(c) < 9 or (14 <= ord(c) < 32)) / len(text)
        density = min(1.0, len(text.strip()) / max(page_area_chars, 1))
    low = confidence < 0.6 or invalid > 0.05 or density < 0.05
    return PageOcrMetrics(
        page=page,
        confidence=confidence,
        invalid_char_ratio=invalid,
        text_density=density,
        low_quality=low,
        extraction_method="ocr",
    )
