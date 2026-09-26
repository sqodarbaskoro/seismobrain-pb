"""
File: test_table_extraction.py
Description: FR-PARSE-03 — structured table cells and Markdown round-trip
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

from seismobrain_ingest.tables import (
    markdown_to_table,
    table_from_cells,
    table_to_markdown,
    tree_node_from_table,
)


def test_table_markdown_round_trip_and_tree_node() -> None:
    table = table_from_cells(
        [
            ["Part", "Qty"],
            ["Sensor", "1"],
            ["Cable", "2"],
        ],
        header_rows=1,
    )
    markdown = table_to_markdown(table)
    assert markdown.splitlines()[0] == "| Part | Qty |"
    assert markdown.splitlines()[1] == "| --- | --- |"
    restored = markdown_to_table(markdown)
    assert restored.cells == table.cells
    assert restored.header_rows == 1
    node = tree_node_from_table(table)
    assert node.type == "table"
    assert node.header_rows == 1
    assert node.cells[0] == ["Part", "Qty"]
    assert "| Sensor | 1 |" in node.text
