"""
File: document_text.py
Description: Extract readable text from stored document bytes via P0/P1 parsers
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-17
Modified: 2026-09-18
Version: 0.2.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from seismobrain_api.text_decode import decode_best_effort, is_text_like
from seismobrain_ingest.document_tree import TreeNode
from seismobrain_ingest.parsers_p1 import build_p1_registry

_PARSER_REGISTRY = build_p1_registry()


def flatten_paragraphs(nodes: list[TreeNode]) -> list[str]:
    texts: list[str] = []
    for node in nodes:
        if node.type == "table" and node.cells:
            texts.extend(" | ".join(row) for row in node.cells if any(row))
        elif node.text.strip():
            texts.append(node.text.strip())
        if node.children:
            texts.extend(flatten_paragraphs(node.children))
    return texts


def flatten_paragraphs_with_headings(
    nodes: list[TreeNode],
) -> list[tuple[str, tuple[str, ...]]]:
    out: list[tuple[str, tuple[str, ...]]] = []
    for node in nodes:
        if node.type == "table" and node.cells:
            out.extend(
                (" | ".join(row), node.heading_path) for row in node.cells if any(row)
            )
        elif node.text.strip():
            out.append((node.text.strip(), node.heading_path))
        if node.children:
            out.extend(flatten_paragraphs_with_headings(node.children))
    return out


def extract_document_sections(
    filename: str, data: bytes
) -> list[tuple[tuple[str, ...], list[str]]]:
    """Group extracted paragraphs into (heading_path, paragraphs) runs, document order.

    Consecutive paragraphs sharing a heading_path (as set by the parser — real
    markdown headings, or numbered PDF headings via assign_pdf_heading_paths) become
    one run; text with no detected heading gets heading_path=().
    """
    if _PARSER_REGISTRY.supports(filename):
        tree = _PARSER_REGISTRY.parse(filename, data)
        pairs = flatten_paragraphs_with_headings(tree.nodes) or [
            (f"({filename} has no extractable text)", ())
        ]
    else:
        text = decode_best_effort(data, filename)
        pairs = [(text, ())]
    sections: list[tuple[tuple[str, ...], list[str]]] = []
    for text, heading_path in pairs:
        if sections and sections[-1][0] == heading_path:
            sections[-1][1].append(text)
        else:
            sections.append((heading_path, [text]))
    return sections


def extract_document_text(filename: str, data: bytes) -> tuple[str, bool]:
    """Return (text, best_effort).

    When a P0/P1 parser supports the format, extract real text and set
    best_effort=False. Otherwise fall back to byte decoding.
    """
    if _PARSER_REGISTRY.supports(filename):
        tree = _PARSER_REGISTRY.parse(filename, data)
        paragraphs = flatten_paragraphs(tree.nodes)
        if paragraphs:
            return "\n\n".join(paragraphs), False
        return f"({filename} has no extractable text)", False
    text = decode_best_effort(data, filename)
    return text, not is_text_like(filename)
