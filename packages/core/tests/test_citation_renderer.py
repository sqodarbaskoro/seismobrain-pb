"""
File: test_citation_renderer.py
Description: Server-rendered citations from trusted metadata (T3.7)
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

from seismobrain_core.citation_renderer import CitationMetadata, render_citations


def test_render_citations_from_trusted_metadata_only() -> None:
    meta = {
        "E1": CitationMetadata(
            evidence_id="E1",
            title="Ops Manual",
            section_path="4.2 Flanges",
            page=12,
            table_ref="Table 3",
            extraction_method="digital",
        )
    }
    rendered = render_citations(["E1", "E9"], metadata=meta)
    assert len(rendered) == 1
    assert rendered[0].title == "Ops Manual"
    assert rendered[0].page == 12
    assert "digital" in rendered[0].display
    assert "manual.pdf" not in rendered[0].display
