"""
File: boilerplate.py
Description: Remove repeated headers/footers/page numbers and configurable boilerplate
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
from collections import Counter

from seismobrain_ingest.document_tree import DocumentTree, TreeNode

_PAGE_NUMBER = re.compile(r"^(?:page\s+)?\d+(?:\s*/\s*\d+)?$", re.IGNORECASE)
_DEFAULT_BOILERPLATE = (
    "table of contents",
    "revision history",
    "document control",
)


def remove_boilerplate(
    tree: DocumentTree,
    *,
    extra_phrases: tuple[str, ...] = (),
) -> DocumentTree:
    """Drop repeated headers/footers, page numbers, and configured boilerplate."""
    phrases = tuple(p.lower() for p in (_DEFAULT_BOILERPLATE + extra_phrases))
    paragraph_texts = [
        n.text.strip() for n in tree.nodes if n.type == "paragraph" and n.text.strip()
    ]
    counts = Counter(paragraph_texts)
    repeated = {text for text, count in counts.items() if count >= 2 and len(text) <= 80}

    kept: list[TreeNode] = []
    for node in tree.nodes:
        if node.type == "paragraph":
            text = node.text.strip()
            if text in repeated:
                continue
            if _PAGE_NUMBER.match(text):
                continue
            if any(phrase in text.lower() for phrase in phrases):
                continue
        if node.type == "section" and any(
            phrase in node.text.lower() for phrase in phrases
        ):
            continue
        if node.type == "table" and node.cells:
            header = " ".join(node.cells[0]).lower()
            if any(phrase in header for phrase in ("revision", "rev ", "version")):
                # Configurable: drop revision tables.
                continue
        kept.append(node)
    return DocumentTree(
        title=tree.title,
        format=tree.format,
        nodes=kept,
        parser_version=tree.parser_version,
    )
