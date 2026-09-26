"""
File: tables.py
Description: Structured table extraction and Markdown serialization (FR-PARSE-03)
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

from seismobrain_ingest.document_tree import TreeNode


@dataclass(frozen=True, slots=True)
class StructuredTable:
    cells: list[list[str]]
    header_rows: int = 1


def table_from_cells(
    cells: list[list[str]],
    *,
    header_rows: int = 1,
) -> StructuredTable:
    if not cells:
        raise ValueError("table requires at least one row")
    width = max(len(row) for row in cells)
    normalized = [row + [""] * (width - len(row)) for row in cells]
    return StructuredTable(cells=normalized, header_rows=header_rows)


def table_to_markdown(table: StructuredTable) -> str:
    if not table.cells:
        return ""
    width = len(table.cells[0])
    lines: list[str] = []
    for index, row in enumerate(table.cells):
        lines.append("| " + " | ".join(row) + " |")
        if index + 1 == table.header_rows:
            lines.append("| " + " | ".join("---" for _ in range(width)) + " |")
    return "\n".join(lines)


def markdown_to_table(markdown: str) -> StructuredTable:
    rows: list[list[str]] = []
    header_rows = 1
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if set(stripped.replace("|", "").replace(":", "").replace("-", "").strip()) == set():
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        rows.append(cells)
    return table_from_cells(rows, header_rows=header_rows)


def tree_node_from_table(table: StructuredTable) -> TreeNode:
    return TreeNode(
        type="table",
        cells=[list(row) for row in table.cells],
        header_rows=table.header_rows,
        text=table_to_markdown(table),
    )
