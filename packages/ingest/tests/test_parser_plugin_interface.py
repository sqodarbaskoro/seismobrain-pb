"""
File: test_parser_plugin_interface.py
Description: FR-PARSE-07 — parser plug-in interface without core changes
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

from seismobrain_ingest.document_tree import DocumentTree, TreeNode
from seismobrain_ingest.parser_plugins import ParserRegistry


class _HtmlStubParser:
    formats = frozenset({"html"})

    def parse(self, filename: str, data: bytes) -> DocumentTree:
        _ = filename
        text = data.decode("utf-8")
        return DocumentTree(
            title="html",
            format="html",
            nodes=[TreeNode(type="paragraph", text=text)],
        )


def test_new_format_registers_without_core_changes() -> None:
    registry = ParserRegistry()
    assert not registry.supports("page.html")
    registry.register(_HtmlStubParser())
    assert registry.supports("page.html")
    tree = registry.parse("page.html", b"<p>hello</p>")
    assert tree.format == "html"
    assert tree.nodes[0].text == "<p>hello</p>"
