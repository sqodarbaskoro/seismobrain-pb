"""
File: format_validation_p1.py
Description: P1 format validation for PPTX/XLSX/RTF/ODT/HTML (FR-DOC-02)
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
from pathlib import PurePosixPath

from seismobrain_ingest.format_validation import (
    FormatValidationError,
    FormatValidationResult,
)

P1_EXTENSIONS = frozenset({".pptx", ".xlsx", ".rtf", ".odt", ".html", ".htm"})
ZIP_MAGIC = b"PK\x03\x04"
RTF_MAGIC = b"{\\rtf"


def validate_p1_upload(
    filename: str,
    data: bytes,
    *,
    max_bytes: int | None = None,
) -> FormatValidationResult:
    extension = PurePosixPath(filename).suffix.lower()
    if extension not in P1_EXTENSIONS:
        raise FormatValidationError(f"unsupported extension: {extension or '(none)'}")
    size_bytes = len(data)
    if max_bytes is not None and size_bytes > max_bytes:
        raise FormatValidationError(f"size exceeds limit ({size_bytes} > {max_bytes})")
    fmt = "html" if extension == ".htm" else extension.lstrip(".")
    if fmt in {"pptx", "xlsx", "odt"}:
        _validate_ooxml_or_odf(data, fmt)
    elif fmt == "rtf":
        if not data.lstrip().startswith(RTF_MAGIC):
            raise FormatValidationError("magic bytes do not match rtf")
    else:
        text = data.decode("utf-8", errors="strict")
        if "<html" not in text.lower() and "<!doctype html" not in text.lower():
            raise FormatValidationError("magic bytes do not match html")
    return FormatValidationResult(format=fmt, size_bytes=size_bytes, page_count=None)


def _validate_ooxml_or_odf(data: bytes, fmt: str) -> None:
    if not data.startswith(ZIP_MAGIC):
        raise FormatValidationError(f"magic bytes do not match {fmt}")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = set(archive.namelist())
    except zipfile.BadZipFile as exc:
        raise FormatValidationError(f"magic bytes do not match {fmt}") from exc
    if fmt == "pptx" and not any(n.startswith("ppt/") for n in names):
        raise FormatValidationError("magic bytes do not match pptx")
    if fmt == "xlsx" and not any(n.startswith("xl/") for n in names):
        raise FormatValidationError("magic bytes do not match xlsx")
    if fmt == "odt" and "mimetype" not in names and "content.xml" not in names:
        raise FormatValidationError("magic bytes do not match odt")
