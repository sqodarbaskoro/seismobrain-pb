"""
File: context_expansion.py
Description: Section-bounded expansion marked context_only (FR-RET-09)
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

from collections.abc import Mapping, Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExpandedSpan:
    text: str
    section_id: str
    context_only: bool
    citable: bool


def expand_within_section(
    *,
    anchor_text: str,
    section_id: str,
    section_paragraphs: Sequence[str],
    verified_sentence_map: Mapping[str, str] | None = None,
) -> list[ExpandedSpan]:
    """Expand using parent section text; expanded spans are context_only by default."""
    verified = verified_sentence_map or {}
    spans: list[ExpandedSpan] = [
        ExpandedSpan(
            text=anchor_text,
            section_id=section_id,
            context_only=False,
            citable=True,
        )
    ]
    for para in section_paragraphs:
        if para == anchor_text:
            continue
        citable = para in verified.values()
        spans.append(
            ExpandedSpan(
                text=para,
                section_id=section_id,
                context_only=True,
                citable=citable,
            )
        )
    return spans
