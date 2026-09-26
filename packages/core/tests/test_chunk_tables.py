"""
File: test_chunk_tables.py
Description: FR-CHK-06 — table row-group chunks and table-summary chunk
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

from seismobrain_core.chunking import SectionInput, chunk_document


def test_table_row_groups_and_summary() -> None:
    rows = tuple((f"p{i}", str(i)) for i in range(20))
    section = SectionInput(
        section_id="t1",
        heading_path=("Parts",),
        table_headers=("Part", "Qty"),
        table_rows=rows,
    )
    result = chunk_document(
        [section], document_title="Manual", table_row_group_size=15
    )
    row_chunks = [c for c in result.children if c.chunk_type == "table_rows"]
    summaries = [c for c in result.children if c.chunk_type == "table_summary"]
    assert len(row_chunks) == 2
    assert all(c.text.startswith("Part | Qty") for c in row_chunks)
    assert len(summaries) == 1
    assert "20 data rows" in summaries[0].text
