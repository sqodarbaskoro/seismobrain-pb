"""
File: test_parse_fixtures_p0.py
Description: FR-PARSE-01 — golden parse fixtures for PDF/DOCX/TXT/MD DocumentTree
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-19
Version: 0.2.1
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import io
from pathlib import Path

from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, StreamObject

from seismobrain_ingest.document_tree import TreeNode
from seismobrain_ingest.parsers_p0 import (
    assign_pdf_heading_paths,
    build_p0_registry,
    extract_pdf_page_texts,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _two_page_pdf_bytes() -> bytes:
    writer = PdfWriter()
    for text in ("Hello page one text.", "Second page content here."):
        page = writer.add_blank_page(width=200, height=200)
        stream = StreamObject()
        stream.set_data(f"BT /F1 12 Tf 10 100 Td ({text}) Tj ET".encode())
        stream_ref = writer._add_object(stream)  # noqa: SLF001 — no public content-stream API
        font = DictionaryObject()
        font[NameObject("/Type")] = NameObject("/Font")
        font[NameObject("/Subtype")] = NameObject("/Type1")
        font[NameObject("/BaseFont")] = NameObject("/Helvetica")
        font_ref = writer._add_object(font)  # noqa: SLF001
        resources = DictionaryObject()
        fontdict = DictionaryObject()
        fontdict[NameObject("/F1")] = font_ref
        resources[NameObject("/Font")] = fontdict
        page[NameObject("/Contents")] = stream_ref
        page[NameObject("/Resources")] = resources
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def _types(nodes: list[TreeNode]) -> set[str]:
    found: set[str] = set()

    def walk(items: list[TreeNode]) -> None:
        for node in items:
            found.add(node.type)
            walk(node.children)

    walk(nodes)
    return found


def test_markdown_fixture_produces_full_document_tree() -> None:
    registry = build_p0_registry()
    data = (FIXTURES / "pilot_procedure.md").read_bytes()
    tree = registry.parse("pilot_procedure.md", data)
    assert tree.format == "md"
    types = _types(tree.nodes)
    assert {
        "section",
        "paragraph",
        "list",
        "list_item",
        "procedure_step",
        "note",
        "warning",
        "caution",
        "table",
        "figure",
        "caption",
    } <= types
    sections = [n for n in tree.nodes if n.type == "section"]
    assert sections[0].heading_path == ("Calibration",)
    assert any(n.type == "procedure_step" and n.attrs.get("step") == "1" for n in tree.nodes)


def test_txt_pdf_docx_fixtures_parse() -> None:
    registry = build_p0_registry()
    txt = registry.parse("plain_notes.txt", (FIXTURES / "plain_notes.txt").read_bytes())
    assert txt.format == "txt"
    assert any(n.type == "procedure_step" for n in txt.nodes)
    assert any(n.type == "note" for n in txt.nodes)

    pdf = registry.parse("calibration.pdf", (FIXTURES / "calibration.pdf").read_bytes())
    assert pdf.format == "pdf"
    assert any("Calibration" in n.text for n in pdf.nodes)

    docx = registry.parse(
        "calibration.docx", (FIXTURES / "calibration.docx").read_bytes()
    )
    assert docx.format == "docx"
    assert any("DOCX calibration body" in n.text for n in docx.nodes)


def test_real_pdf_uses_pypdf_extraction_not_regex_fallback() -> None:
    """A well-formed PDF (valid xref/trailer) must go through real text
    extraction, not the regex fallback meant only for malformed fixtures."""
    registry = build_p0_registry()
    data = (FIXTURES / "device_controller_real.pdf").read_bytes()
    tree = registry.parse("device_controller_real.pdf", data)
    assert tree.format == "pdf"
    assert any(
        "Device Controller monitors sensor volt levels." in n.text
        for n in tree.nodes
    )


def test_extract_pdf_page_texts_returns_real_per_page_text() -> None:
    pages = extract_pdf_page_texts(_two_page_pdf_bytes())
    assert [p.page for p in pages] == [1, 2]
    assert "Hello page one text." in pages[0].text
    assert "Second page content here." in pages[1].text


def test_extract_pdf_page_texts_empty_for_malformed_pdf() -> None:
    assert extract_pdf_page_texts(b"not a pdf") == []


def test_numbered_heading_opens_a_heading_path_for_following_paragraphs() -> None:
    paragraphs = [
        "1.3 Section Editor",
        "The Section Editor is used to insert or delete section markers.",
        "1.4 Section Renumbering",
        "Section numbers are renumbered from the anchor marker.",
    ]
    result = assign_pdf_heading_paths(paragraphs)
    assert result[0] == ("1.3 Section Editor", ("1.3 Section Editor",))
    assert result[1] == (
        "The Section Editor is used to insert or delete section markers.",
        ("1.3 Section Editor",),
    )
    assert result[2] == ("1.4 Section Renumbering", ("1.4 Section Renumbering",))
    assert result[3] == (
        "Section numbers are renumbered from the anchor marker.",
        ("1.4 Section Renumbering",),
    )


def test_ordinary_sentence_starting_with_a_number_is_not_a_heading() -> None:
    paragraphs = [
        "2 technicians verified the calibration readings before the survey began today.",
    ]
    result = assign_pdf_heading_paths(paragraphs)
    assert result == [(paragraphs[0], ())]
