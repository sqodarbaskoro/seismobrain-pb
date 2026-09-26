"""
File: test_format_validation_p1.py
Description: P1 format validation PPTX/XLSX/RTF/ODT/HTML (T5.11)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-18
Version: 0.1.1
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import io
import zipfile

import pytest

from seismobrain_ingest.format_validation import FormatValidationError
from seismobrain_ingest.format_validation_p1 import validate_p1_upload


def _zip_with(paths: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in paths.items():
            zf.writestr(name, content)
    return buf.getvalue()


def test_accepts_p1_formats() -> None:
    assert (
        validate_p1_upload(
            "a.pptx", _zip_with({"ppt/slides/slide1.xml": "<p>hi</p>"})
        ).format
        == "pptx"
    )
    assert (
        validate_p1_upload(
            "a.xlsx", _zip_with({"xl/workbook.xml": "<workbook/>"})
        ).format
        == "xlsx"
    )
    assert validate_p1_upload("a.rtf", b"{\\rtf1 hello}").format == "rtf"
    assert (
        validate_p1_upload(
            "a.odt",
            _zip_with(
                {
                    "mimetype": "application/vnd.oasis.opendocument.text",
                    "content.xml": "<office/>",
                }
            ),
        ).format
        == "odt"
    )
    assert validate_p1_upload("a.html", b"<html><title>T</title></html>").format == "html"


def test_rejects_bad_p1_magic() -> None:
    with pytest.raises(FormatValidationError):
        validate_p1_upload("a.pptx", b"not-zip")
