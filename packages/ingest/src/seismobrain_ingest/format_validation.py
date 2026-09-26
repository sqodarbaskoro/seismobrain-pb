"""
File: format_validation.py
Description: P0 upload format validation — extension, magic bytes, size, pages, encryption
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
from dataclasses import dataclass
from pathlib import PurePosixPath

P0_EXTENSIONS = frozenset({".pdf", ".docx", ".doc", ".txt", ".md"})
DEFAULT_MAX_PAGES = 10_000
OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
ZIP_MAGIC = b"PK\x03\x04"
PDF_MAGIC = b"%PDF"


class FormatValidationError(ValueError):
    """Raised when an upload fails P0 format / SEC-08 checks."""


@dataclass(frozen=True, slots=True)
class FormatValidationResult:
    format: str
    size_bytes: int
    page_count: int | None


def validate_p0_upload(
    filename: str,
    data: bytes,
    *,
    max_bytes: int | None = None,
    max_pages: int = DEFAULT_MAX_PAGES,
) -> FormatValidationResult:
    """Validate P0 formats via extension + magic bytes, size, pages, encryption."""
    extension = PurePosixPath(filename).suffix.lower()
    if extension not in P0_EXTENSIONS:
        raise FormatValidationError(f"unsupported extension: {extension or '(none)'}")

    size_bytes = len(data)
    if max_bytes is not None and size_bytes > max_bytes:
        raise FormatValidationError(f"size exceeds limit ({size_bytes} > {max_bytes})")

    fmt = extension.lstrip(".")
    if fmt == "pdf":
        _validate_pdf(data, max_pages=max_pages)
        pages = data.count(b"/Type /Page")
        return FormatValidationResult(format="pdf", size_bytes=size_bytes, page_count=pages)
    if fmt == "docx":
        _validate_docx(data)
        return FormatValidationResult(format="docx", size_bytes=size_bytes, page_count=None)
    if fmt == "doc":
        _validate_doc(data)
        return FormatValidationResult(format="doc", size_bytes=size_bytes, page_count=None)
    _validate_text(data)
    return FormatValidationResult(format=fmt, size_bytes=size_bytes, page_count=None)


def _validate_pdf(data: bytes, *, max_pages: int) -> None:
    if not data.startswith(PDF_MAGIC):
        raise FormatValidationError("magic bytes do not match pdf")
    if b"/Encrypt" in data:
        raise FormatValidationError("encrypted pdf is not accepted")
    pages = data.count(b"/Type /Page")
    if pages > max_pages:
        raise FormatValidationError(f"page count exceeds limit ({pages} > {max_pages})")


def _validate_docx(data: bytes) -> None:
    if not data.startswith(ZIP_MAGIC):
        raise FormatValidationError("magic bytes do not match docx")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = set(archive.namelist())
    except zipfile.BadZipFile as exc:
        raise FormatValidationError("magic bytes do not match docx") from exc
    if "[Content_Types].xml" not in names or not any(
        name.startswith("word/") for name in names
    ):
        raise FormatValidationError("magic bytes do not match docx")


def _validate_doc(data: bytes) -> None:
    if not data.startswith(OLE_MAGIC):
        raise FormatValidationError("magic bytes do not match doc")


def _validate_text(data: bytes) -> None:
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FormatValidationError("magic bytes do not match text") from exc
