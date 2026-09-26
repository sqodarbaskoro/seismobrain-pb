"""
File: parsers_p1.py
Description: P1 parsers for PPTX/XLSX/RTF/ODT/HTML (FR-PARSE-07)
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
import re
import zipfile
from pathlib import PurePosixPath

from seismobrain_ingest.document_tree import DocumentTree, TreeNode
from seismobrain_ingest.parser_plugins import ParserRegistry
from seismobrain_ingest.parsers_p0 import build_p0_registry


def build_p1_registry() -> ParserRegistry:
    registry = build_p0_registry()
    registry.register(_HtmlParser())
    registry.register(_RtfParser())
    registry.register(_ZipTextStubParser(frozenset({"pptx"}), "ppt/"))
    registry.register(_ZipTextStubParser(frozenset({"xlsx"}), "xl/"))
    registry.register(_ZipTextStubParser(frozenset({"odt"}), "content.xml"))
    return registry


class _HtmlParser:
    formats = frozenset({"html", "htm"})

    def parse(self, filename: str, data: bytes) -> DocumentTree:
        text = data.decode("utf-8")
        title_m = re.search(r"<title>(.*?)</title>", text, re.I | re.S)
        title = title_m.group(1).strip() if title_m else PurePosixPath(filename).stem
        body = re.sub(r"<[^>]+>", " ", text)
        body = re.sub(r"\s+", " ", body).strip()
        return DocumentTree(
            title=title,
            format="html",
            nodes=[TreeNode(type="paragraph", text=body)],
            parser_version="p1-1",
        )


class _RtfParser:
    formats = frozenset({"rtf"})

    def parse(self, filename: str, data: bytes) -> DocumentTree:
        raw = data.decode("latin-1", errors="replace")
        text = re.sub(r"\\[a-z]+\d* ?", "", raw)
        text = text.replace("{", "").replace("}", "")
        text = re.sub(r"\s+", " ", text).strip()
        return DocumentTree(
            title=PurePosixPath(filename).stem,
            format="rtf",
            nodes=[TreeNode(type="paragraph", text=text)],
            parser_version="p1-1",
        )


class _ZipTextStubParser:
    def __init__(self, formats: frozenset[str], marker: str) -> None:
        self.formats = formats
        self._marker = marker

    def parse(self, filename: str, data: bytes) -> DocumentTree:
        fmt = PurePosixPath(filename).suffix.lower().lstrip(".")
        texts: list[str] = []
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for name in archive.namelist():
                if self._marker in name and name.endswith((".xml", ".txt")):
                    try:
                        chunk = archive.read(name).decode("utf-8", errors="ignore")
                    except KeyError:
                        continue
                    plain = re.sub(r"<[^>]+>", " ", chunk)
                    plain = re.sub(r"\s+", " ", plain).strip()
                    if plain:
                        texts.append(plain)
        body = " ".join(texts) or f"{fmt} document"
        return DocumentTree(
            title=PurePosixPath(filename).stem,
            format=fmt,
            nodes=[TreeNode(type="paragraph", text=body)],
            parser_version="p1-1",
        )
