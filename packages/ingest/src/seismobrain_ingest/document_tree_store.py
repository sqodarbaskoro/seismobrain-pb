"""
File: document_tree_store.py
Description: Persist versioned DocumentTree intermediates (FR-ING-11)
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

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

from seismobrain_ingest.document_tree import DocumentTree, NodeType, TreeNode


class DocumentTreeStore:
    """Filesystem store for versioned DocumentTree JSON intermediates."""

    def __init__(self, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    def put(self, *, version_id: str, parser_version: str, tree: DocumentTree) -> Path:
        path = self._path(version_id, parser_version)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version_id": version_id,
            "parser_version": parser_version,
            "tree": asdict(tree),
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def get(self, *, version_id: str, parser_version: str) -> DocumentTree:
        path = self._path(version_id, parser_version)
        payload = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
        raw = cast(dict[str, Any], payload["tree"])
        nodes_raw = cast(list[dict[str, Any]], raw.get("nodes", []))
        return DocumentTree(
            title=str(raw["title"]),
            format=str(raw["format"]),
            parser_version=str(raw.get("parser_version", parser_version)),
            nodes=[_node_from_dict(n) for n in nodes_raw],
        )

    def exists(self, *, version_id: str, parser_version: str) -> bool:
        return self._path(version_id, parser_version).is_file()

    def _path(self, version_id: str, parser_version: str) -> Path:
        safe_parser = parser_version.replace("/", "_")
        return self._root / version_id / f"{safe_parser}.tree.json"


def _node_from_dict(raw: dict[str, Any]) -> TreeNode:
    children_raw = cast(list[dict[str, Any]], raw.get("children", []))
    cells_raw = cast(list[list[Any]], raw.get("cells", []))
    heading_raw = cast(list[Any], raw.get("heading_path", []))
    attrs_raw = cast(dict[str, Any], raw.get("attrs", {}))
    level_raw = raw.get("level")
    level = int(level_raw) if level_raw is not None else None
    return TreeNode(
        type=cast(NodeType, str(raw["type"])),
        text=str(raw.get("text", "")),
        level=level,
        heading_path=tuple(str(part) for part in heading_raw),
        children=[_node_from_dict(child) for child in children_raw],
        cells=[[str(cell) for cell in row] for row in cells_raw],
        header_rows=int(raw.get("header_rows", 0)),
        attrs={str(key): str(value) for key, value in attrs_raw.items()},
    )
