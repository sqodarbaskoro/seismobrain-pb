"""
File: parsers_p0.py
Description: P0 parsers for PDF, DOCX, TXT, MD into DocumentTree (FR-PARSE-01)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-19
Version: 0.3.1
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import io
import re
from pathlib import PurePosixPath

import pypdf

from seismobrain_ingest.document_tree import DocumentTree, TreeNode
from seismobrain_ingest.page_mapping import PageText
from seismobrain_ingest.parser_plugins import ParserRegistry


def build_p0_registry() -> ParserRegistry:
    registry = ParserRegistry()
    registry.register(_TextMarkdownParser())
    registry.register(_PdfStubParser())
    registry.register(_DocxStubParser())
    return registry


class _TextMarkdownParser:
    formats = frozenset({"txt", "md"})

    def parse(self, filename: str, data: bytes) -> DocumentTree:
        text = data.decode("utf-8")
        fmt = PurePosixPath(filename).suffix.lower().lstrip(".")
        title = PurePosixPath(filename).stem
        nodes: list[TreeNode] = []
        heading_path: list[str] = []
        list_items: list[TreeNode] = []

        def flush_list() -> None:
            nonlocal list_items
            if list_items:
                nodes.append(TreeNode(type="list", children=list(list_items)))
                list_items = []

        for raw_line in text.splitlines():
            line = raw_line.rstrip()
            if not line.strip():
                flush_list()
                continue
            heading = re.match(r"^(#{1,6})\s+(.*)$", line)
            if heading:
                flush_list()
                level = len(heading.group(1))
                name = heading.group(2).strip()
                heading_path = heading_path[: level - 1] + [name]
                nodes.append(
                    TreeNode(
                        type="section",
                        text=name,
                        level=level,
                        heading_path=tuple(heading_path),
                    )
                )
                continue
            if re.match(r"^[-*]\s+", line):
                list_items.append(
                    TreeNode(
                        type="list_item",
                        text=re.sub(r"^[-*]\s+", "", line),
                        heading_path=tuple(heading_path),
                    )
                )
                continue
            step = re.match(r"^Step\s+(\d+)[:.]\s*(.*)$", line, re.IGNORECASE)
            if step:
                flush_list()
                nodes.append(
                    TreeNode(
                        type="procedure_step",
                        text=step.group(2),
                        attrs={"step": step.group(1)},
                        heading_path=tuple(heading_path),
                    )
                )
                continue
            note = re.match(r"^(NOTE|WARNING|CAUTION):\s*(.*)$", line, re.IGNORECASE)
            if note:
                flush_list()
                kind = note.group(1).lower()
                if kind == "warning":
                    nodes.append(
                        TreeNode(
                            type="warning",
                            text=note.group(2),
                            heading_path=tuple(heading_path),
                        )
                    )
                elif kind == "caution":
                    nodes.append(
                        TreeNode(
                            type="caution",
                            text=note.group(2),
                            heading_path=tuple(heading_path),
                        )
                    )
                else:
                    nodes.append(
                        TreeNode(
                            type="note",
                            text=note.group(2),
                            heading_path=tuple(heading_path),
                        )
                    )
                continue
            table = re.match(r"^\|(.+)\|$", line)
            if table and "---" not in line:
                flush_list()
                cells = [[c.strip() for c in table.group(1).split("|")]]
                nodes.append(
                    TreeNode(
                        type="table",
                        cells=cells,
                        header_rows=1,
                        heading_path=tuple(heading_path),
                    )
                )
                continue
            figure = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", line)
            if figure:
                flush_list()
                nodes.append(
                    TreeNode(
                        type="figure",
                        text=figure.group(2),
                        attrs={"alt": figure.group(1)},
                        heading_path=tuple(heading_path),
                    )
                )
                nodes.append(
                    TreeNode(
                        type="caption",
                        text=figure.group(1),
                        heading_path=tuple(heading_path),
                    )
                )
                continue
            flush_list()
            nodes.append(
                TreeNode(
                    type="paragraph",
                    text=line,
                    heading_path=tuple(heading_path),
                )
            )
        flush_list()
        return DocumentTree(title=title, format=fmt, nodes=nodes)


_PDF_HEADING_RE = re.compile(r"^\d+(?:\.\d+)*\s+\S")
_PDF_HEADING_MAX_WORDS = 8


def assign_pdf_heading_paths(
    paragraphs: list[str],
) -> list[tuple[str, tuple[str, ...]]]:
    """A short numbered line ("1.3 Section Editor") opens a heading_path that following
    text inherits until the next heading — mirrors the markdown parser's heading_path
    tracking, for PDFs whose numbered sections are plain text with no real markup.

    A heading is only ever the first *line* of a paragraph block (pypdf commonly joins
    a heading and the body that follows it with a single newline, without a blank line
    between them); the rest of the block is kept as one body paragraph so a wrapped
    sentence is never split mid-sentence.
    """
    stack: list[tuple[int, str]] = []
    out: list[tuple[str, tuple[str, ...]]] = []
    for block in paragraphs:
        first_line, _, rest = block.partition("\n")
        number = first_line.split(" ", 1)[0] if first_line else ""
        if (
            _PDF_HEADING_RE.match(first_line)
            and len(first_line.split()) <= _PDF_HEADING_MAX_WORDS
        ):
            depth = number.count(".") + 1
            while stack and stack[-1][0] >= depth:
                stack.pop()
            stack.append((depth, first_line))
            out.append((first_line, tuple(text for _, text in stack)))
            if rest.strip():
                out.append((rest.strip(), tuple(text for _, text in stack)))
        else:
            out.append((block, tuple(text for _, text in stack)))
    return out


def extract_pdf_page_texts(data: bytes) -> list[PageText]:
    """Real per-PDF-page text via pypdf; [] for malformed/non-PDF bytes."""
    try:
        reader = pypdf.PdfReader(io.BytesIO(data))
        return [
            PageText(page=index + 1, text=page.extract_text() or "")
            for index, page in enumerate(reader.pages)
        ]
    except Exception:
        # Malformed / fixture PDFs (missing xref, truncated stream, etc.)
        return []


class _PdfStubParser:
    formats = frozenset({"pdf"})

    def parse(self, filename: str, data: bytes) -> DocumentTree:
        paragraphs = self._extract_with_pypdf(data) or self._extract_with_regex(data)
        return DocumentTree(
            title=PurePosixPath(filename).stem,
            format="pdf",
            nodes=paragraphs
            or [TreeNode(type="paragraph", text="(empty pdf fixture)")],
        )

    @staticmethod
    def _extract_with_pypdf(data: bytes) -> list[TreeNode]:
        pages = extract_pdf_page_texts(data)
        paragraphs = [
            paragraph.strip()
            for page in pages
            for paragraph in re.split(r"\n\s*\n", page.text)
            if paragraph.strip()
        ]
        return [
            TreeNode(type="paragraph", text=text, heading_path=heading_path)
            for text, heading_path in assign_pdf_heading_paths(paragraphs)
        ]

    @staticmethod
    def _extract_with_regex(data: bytes) -> list[TreeNode]:
        # Lightweight digital-text extraction for fixture PDFs that embed plain text
        # without a valid xref/trailer (pypdf refuses those).
        text = data.decode("latin-1", errors="ignore")
        paragraphs = [
            TreeNode(type="paragraph", text=chunk.strip())
            for chunk in re.findall(r"BT\s*/F\d+\s+\d+\s+Tf\s*\((.*?)\)\s*Tj\s*ET", text)
            if chunk.strip()
        ]
        if not paragraphs:
            # Fall back to any readable ASCII runs for minimal fixtures.
            runs = re.findall(r"[A-Za-z][A-Za-z0-9 ,.;:'-]{3,}", text)
            paragraphs = [TreeNode(type="paragraph", text=run) for run in runs[:20]]
        return paragraphs


class _DocxStubParser:
    formats = frozenset({"docx"})

    def parse(self, filename: str, data: bytes) -> DocumentTree:
        import io
        import zipfile

        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            xml = archive.read("word/document.xml").decode("utf-8")
        texts = re.findall(r"<w:t[^>]*>(.*?)</w:t>", xml)
        joined = " ".join(t.strip() for t in texts if t.strip())
        nodes: list[TreeNode] = []
        if joined:
            nodes.append(TreeNode(type="paragraph", text=joined))
        return DocumentTree(
            title=PurePosixPath(filename).stem,
            format="docx",
            nodes=nodes or [TreeNode(type="paragraph", text="(empty docx)")],
        )
