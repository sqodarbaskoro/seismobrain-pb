"""
File: page_mapping.py
Description: Word-to-PDF page mapping by text alignment with confidence (FR-ING-08)
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
class PageText:
    page: int
    text: str


@dataclass(frozen=True, slots=True)
class ChunkPageMap:
    chunk_id: str
    page: int | None
    confidence: float
    citation_mode: str  # "page" | "section_only"


def map_chunk_to_page(
    *,
    chunk_id: str,
    chunk_text: str,
    pages: list[PageText],
    confidence_threshold: float = 0.55,
) -> ChunkPageMap:
    """Align chunk text to PDF rendition pages; low confidence → section-only."""
    if not pages:
        return ChunkPageMap(
            chunk_id=chunk_id, page=None, confidence=0.0, citation_mode="section_only"
        )
    needle = " ".join(chunk_text.lower().split())
    if not needle:
        return ChunkPageMap(
            chunk_id=chunk_id, page=None, confidence=0.0, citation_mode="section_only"
        )
    best_page: int | None = None
    best_score = 0.0
    for page in pages:
        hay = " ".join(page.text.lower().split())
        if not hay:
            continue
        if needle in hay:
            score = min(1.0, len(needle) / max(len(hay), 1))
            # Exact containment scores high.
            score = max(score, 0.9)
        else:
            # Token overlap ratio.
            n_tokens = set(needle.split())
            h_tokens = set(hay.split())
            if not n_tokens:
                continue
            score = len(n_tokens & h_tokens) / len(n_tokens)
        if score > best_score:
            best_score = score
            best_page = page.page
    if best_page is None or best_score < confidence_threshold:
        return ChunkPageMap(
            chunk_id=chunk_id,
            page=None,
            confidence=best_score,
            citation_mode="section_only",
        )
    return ChunkPageMap(
        chunk_id=chunk_id,
        page=best_page,
        confidence=best_score,
        citation_mode="page",
    )


def render_word_to_pdf_stub(docx_bytes: bytes) -> bytes:
    """Placeholder rendition writer; production uses sandboxed LibreOffice (DR-08)."""
    _ = docx_bytes
    return b"%PDF-1.4\n% SeismoBrain Word rendition stub\n%%EOF\n"
