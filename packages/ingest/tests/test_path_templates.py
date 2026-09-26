"""
File: test_path_templates.py
Description: Path templates map folder structure to metadata (T5.17)
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

from seismobrain_ingest.path_templates import apply_path_template


def test_path_template_extracts_metadata_fields() -> None:
    result = apply_path_template(
        "alpha/manuals/seal-procedure.pdf",
        "{plant}/{doc_type}/{title}.pdf",
    )
    assert result.matched is True
    assert result.fields == {
        "plant": "alpha",
        "doc_type": "manuals",
        "title": "seal-procedure",
    }
    miss = apply_path_template("x.pdf", "{plant}/{doc_type}/{title}.pdf")
    assert miss.matched is False
