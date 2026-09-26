"""
File: text_decode.py
Description: Best-effort text decoding shared by ingestion and document preview
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-17
Modified: 2026-09-17
Version: 0.2.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

_TEXT_SUFFIXES = (".md", ".txt", ".csv", ".json", ".html", ".xml")


def decode_best_effort(data: bytes, filename: str) -> str:
    """Decode bytes to text when no format parser applies.

    Prefer ``document_text.extract_document_text`` for preview/ingest — that path
    uses P0/P1 parsers (PDF, DOCX, …) and only falls back here for unknown types.
    """
    lower = filename.lower()
    if lower.endswith(_TEXT_SUFFIXES):
        return data.decode("utf-8", errors="replace")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1", errors="replace")


def is_text_like(filename: str) -> bool:
    return filename.lower().endswith(_TEXT_SUFFIXES)
