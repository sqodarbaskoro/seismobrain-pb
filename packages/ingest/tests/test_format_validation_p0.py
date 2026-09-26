"""
File: test_format_validation_p0.py
Description: FR-DOC-02 / SEC-08 — P0 format extension, magic bytes, size, pages, encryption
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

import io
import zipfile

import pytest

from seismobrain_ingest.format_validation import (
    FormatValidationError,
    validate_p0_upload,
)


def _minimal_pdf(*, pages: int = 1, encrypted: bool = False) -> bytes:
    # Intentionally tiny PDF-like bytes for magic/page/encrypt checks (not a full PDF).
    body = b"%PDF-1.4\n"
    if encrypted:
        body += b"1 0 obj<< /Encrypt 2 0 R >>endobj\n"
    for index in range(pages):
        body += f"{10 + index} 0 obj<< /Type /Page /Parent 3 0 R >>endobj\n".encode()
    body += b"%%EOF\n"
    return body


def _docx_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>',
        )
        archive.writestr("word/document.xml", "<w:document></w:document>")
    return buffer.getvalue()


def _ole_doc_bytes() -> bytes:
    return b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 64


def test_accepts_p0_formats() -> None:
    assert validate_p0_upload("a.pdf", _minimal_pdf()).format == "pdf"
    assert validate_p0_upload("a.docx", _docx_bytes()).format == "docx"
    assert validate_p0_upload("a.doc", _ole_doc_bytes()).format == "doc"
    assert validate_p0_upload("a.txt", b"plain text").format == "txt"
    assert validate_p0_upload("a.md", b"# Title\n").format == "md"


def test_rejects_extension_magic_mismatch() -> None:
    with pytest.raises(FormatValidationError, match="magic"):
        validate_p0_upload("spoof.pdf", b"not a pdf")
    with pytest.raises(FormatValidationError, match="magic"):
        validate_p0_upload("spoof.docx", b"PK\x03\x04not-a-docx")


def test_rejects_unsupported_extension() -> None:
    with pytest.raises(FormatValidationError, match="unsupported"):
        validate_p0_upload("a.exe", b"MZ")


def test_rejects_oversize_and_page_limit() -> None:
    with pytest.raises(FormatValidationError, match="size"):
        validate_p0_upload("a.pdf", _minimal_pdf(), max_bytes=10)
    with pytest.raises(FormatValidationError, match="page"):
        validate_p0_upload(
            "a.pdf",
            _minimal_pdf(pages=5),
            max_pages=3,
        )


def test_rejects_encrypted_pdf() -> None:
    with pytest.raises(FormatValidationError, match="encrypted"):
        validate_p0_upload("secret.pdf", _minimal_pdf(encrypted=True))
