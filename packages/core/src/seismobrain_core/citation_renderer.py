"""
File: citation_renderer.py
Description: Server-rendered citations from trusted metadata (FR-GEN-06)
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
class CitationMetadata:
    evidence_id: str
    title: str
    section_path: str
    page: int | None
    table_ref: str | None
    extraction_method: str
    # Retrieval relevance in [0, 1], highest-ranked = 1.0. Defaulted so existing
    # call sites (tests, export_routes.py) that predate this field keep working.
    relevance: float = 1.0


@dataclass(frozen=True, slots=True)
class RenderedCitation:
    evidence_id: str
    display: str
    title: str
    section_path: str
    page: int | None
    table_ref: str | None
    extraction_method: str
    relevance: float = 1.0


def render_citations(
    evidence_ids: Sequence[str],
    *,
    metadata: Mapping[str, CitationMetadata],
) -> list[RenderedCitation]:
    """Render citations only from trusted server metadata (never LLM-authored)."""
    out: list[RenderedCitation] = []
    for eid in evidence_ids:
        meta = metadata.get(eid)
        if meta is None:
            continue
        parts = [meta.title]
        if meta.section_path:
            parts.append(meta.section_path)
        if meta.page is not None:
            parts.append(f"p.{meta.page}")
        if meta.table_ref:
            parts.append(meta.table_ref)
        parts.append(meta.extraction_method)
        out.append(
            RenderedCitation(
                evidence_id=eid,
                display=" · ".join(parts),
                title=meta.title,
                section_path=meta.section_path,
                page=meta.page,
                table_ref=meta.table_ref,
                extraction_method=meta.extraction_method,
                relevance=meta.relevance,
            )
        )
    return out
