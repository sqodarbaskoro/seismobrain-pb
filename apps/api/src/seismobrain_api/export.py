"""
File: export.py
Description: Export conversation answers to Markdown/PDF with citations (FR-CHAT-07)
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

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from seismobrain_core.citation_renderer import CitationMetadata, render_citations


@dataclass(frozen=True, slots=True)
class ExportSentence:
    text: str
    evidence_ids: tuple[str, ...]


def export_markdown(
    *,
    title: str,
    sentences: Sequence[ExportSentence],
    citations: Mapping[str, CitationMetadata],
) -> str:
    lines = [f"# {title}", ""]
    used: list[str] = []
    for sentence in sentences:
        lines.append(sentence.text)
        for eid in sentence.evidence_ids:
            if eid not in used:
                used.append(eid)
        lines.append("")
    rendered = render_citations(used, metadata=citations)
    if rendered:
        lines.append("## Citations")
        for cite in rendered:
            lines.append(f"- [{cite.evidence_id}] {cite.display}")
        lines.append("")
    return "\n".join(lines)


def export_pdf(
    *,
    title: str,
    sentences: Sequence[ExportSentence],
    citations: Mapping[str, CitationMetadata],
) -> bytes:
    """Minimal PDF (Type1 Helvetica) embedding markdown body as text lines."""
    md = export_markdown(title=title, sentences=sentences, citations=citations)
    # Escape PDF string specials
    safe_lines = []
    for line in md.splitlines():
        safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        safe_lines.append(safe[:110])
    content_lines = ["BT", "/F1 10 Tf", "50 750 Td", "12 TL"]
    for i, line in enumerate(safe_lines):
        if i == 0:
            content_lines.append(f"({line}) Tj")
        else:
            content_lines.append("T*")
            content_lines.append(f"({line}) Tj")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects: list[bytes] = []
    objects.append(b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n")
    objects.append(b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n")
    objects.append(
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>endobj\n"
    )
    objects.append(
        f"4 0 obj<< /Length {len(stream)} >>stream\n".encode()
        + stream
        + b"\nendstream\nendobj\n"
    )
    objects.append(
        b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n"
    )

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(out))
        out.extend(obj)
    xref_pos = len(out)
    out.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode())
    out.extend(
        f"trailer<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_pos}\n%%EOF\n".encode()
    )
    return bytes(out)
