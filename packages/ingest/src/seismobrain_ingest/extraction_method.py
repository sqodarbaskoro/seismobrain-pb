"""
File: extraction_method.py
Description: Record extraction_method and quality score on chunks (FR-ING-07)
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
from typing import Literal

ExtractionMethod = Literal["digital", "ocr", "vision"]


@dataclass(frozen=True, slots=True)
class ChunkExtractionMeta:
    chunk_id: str
    extraction_method: ExtractionMethod
    quality_score: float


def digital_extraction_meta(chunk_id: str, *, text: str) -> ChunkExtractionMeta:
    """P0 path: digital extraction with a simple printable-character quality score."""
    if not text:
        score = 0.0
    else:
        printable = sum(1 for ch in text if ch.isprintable() or ch.isspace())
        score = printable / len(text)
    return ChunkExtractionMeta(
        chunk_id=chunk_id,
        extraction_method="digital",
        quality_score=round(score, 4),
    )
