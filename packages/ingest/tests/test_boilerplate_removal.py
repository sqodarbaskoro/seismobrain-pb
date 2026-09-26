"""
File: test_boilerplate_removal.py
Description: FR-PARSE-02 — remove headers, footers, page numbers, boilerplate
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

from seismobrain_ingest.boilerplate import remove_boilerplate
from seismobrain_ingest.document_tree import DocumentTree, TreeNode


def test_removes_repeated_headers_footers_page_numbers_and_toc() -> None:
    tree = DocumentTree(
        title="doc",
        format="md",
        nodes=[
            TreeNode(type="paragraph", text="Acme Corp Confidential"),
            TreeNode(type="paragraph", text="Real content one"),
            TreeNode(type="paragraph", text="Page 2"),
            TreeNode(type="paragraph", text="Acme Corp Confidential"),
            TreeNode(type="section", text="Table of Contents", level=1),
            TreeNode(type="paragraph", text="Real content two"),
            TreeNode(
                type="table",
                cells=[["Revision", "Date"], ["1.0", "2024-01-01"]],
                header_rows=1,
            ),
            TreeNode(type="paragraph", text="3 / 10"),
        ],
    )
    cleaned = remove_boilerplate(tree)
    texts = [n.text for n in cleaned.nodes]
    assert "Acme Corp Confidential" not in texts
    assert "Page 2" not in texts
    assert "3 / 10" not in texts
    assert "Table of Contents" not in texts
    assert "Real content one" in texts
    assert "Real content two" in texts
    assert not any(n.type == "table" for n in cleaned.nodes)
