"""
File: document_tree.py
Description: DocumentTree domain model for parsed document structure (FR-PARSE-01)
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

from dataclasses import dataclass, field
from typing import Literal

NodeType = Literal[
    "section",
    "paragraph",
    "list",
    "list_item",
    "procedure_step",
    "note",
    "warning",
    "caution",
    "table",
    "figure",
    "caption",
]


@dataclass(slots=True)
class TreeNode:
    type: NodeType
    text: str = ""
    level: int | None = None
    heading_path: tuple[str, ...] = ()
    children: list[TreeNode] = field(default_factory=list)
    cells: list[list[str]] = field(default_factory=list)
    header_rows: int = 0
    attrs: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class DocumentTree:
    title: str
    format: str
    nodes: list[TreeNode] = field(default_factory=list)
    parser_version: str = "0.1.0"
