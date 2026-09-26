"""
File: evidence_tag_lint.py
Description: Lint LLM output for E-tags; ban filenames/pages/sections (FR-GEN-02)
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

import re
from dataclasses import dataclass

_FILENAME = re.compile(
    r"\b[\w\-]+\.(?:pdf|docx|doc|pptx|xlsx|txt|md)\b", re.IGNORECASE
)
_PAGE_CITATION = re.compile(r"\b(?:page|p\.|pp\.)\s*\d+\b", re.IGNORECASE)
_SECTION_CITATION = re.compile(r"\b(?:section|§)\s*[\d.]+\b", re.IGNORECASE)
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_TERMINAL_ETAGS = re.compile(r"\[E\d+\](?:\[E\d+\])*\s*$")


@dataclass(frozen=True, slots=True)
class LintResult:
    ok: bool
    errors: tuple[str, ...]


def lint_evidence_tags(text: str, *, allow_insufficient: bool = True) -> LintResult:
    """Every factual sentence must end with [E#]; no filename/page/section citations."""
    stripped = text.strip()
    if allow_insufficient and stripped == "INSUFFICIENT_EVIDENCE":
        return LintResult(ok=True, errors=())
    errors: list[str] = []
    if _FILENAME.search(text):
        errors.append("filename_citation")
    if _PAGE_CITATION.search(text):
        errors.append("page_citation")
    if _SECTION_CITATION.search(text):
        errors.append("section_citation")
    sentences = [s.strip() for s in _SENTENCE_END.split(stripped) if s.strip()]
    if not sentences:
        errors.append("empty")
    for sentence in sentences:
        if not _TERMINAL_ETAGS.search(sentence):
            errors.append(f"missing_or_nonterminal_etag:{sentence[:40]}")
    return LintResult(ok=not errors, errors=tuple(errors))
