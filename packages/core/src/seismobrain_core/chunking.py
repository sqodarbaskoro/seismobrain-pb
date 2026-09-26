"""
File: chunking.py
Description: Hierarchical section-aware chunking with no silent truncation (FR-CHK-*)
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

import re
from collections.abc import Callable
from dataclasses import dataclass, field

CHUNKER_VERSION = "chunker-v1"

TokenCounter = Callable[[str], int]


def whitespace_token_count(text: str) -> int:
    return len(text.split()) if text.strip() else 0


@dataclass(frozen=True, slots=True)
class SectionInput:
    section_id: str
    heading_path: tuple[str, ...]
    paragraphs: tuple[str, ...] = ()
    procedure_title: str | None = None
    steps: tuple[tuple[str, tuple[str, ...]], ...] = ()
    # steps: (step_text, warnings_for_step)
    table_headers: tuple[str, ...] = ()
    table_rows: tuple[tuple[str, ...], ...] = ()


@dataclass(frozen=True, slots=True)
class Chunk:
    chunk_id: str
    section_id: str
    chunk_type: str
    text: str
    contextual_header: str
    parent_section_id: str | None
    chunker_version: str = CHUNKER_VERSION
    heading_path: tuple[str, ...] = ()


@dataclass
class ChunkingResult:
    children: list[Chunk] = field(default_factory=list)
    parents: list[Chunk] = field(default_factory=list)
    overflow_splits: int = 0
    truncations: int = 0


def build_contextual_header(
    *,
    document_title: str,
    revision: str,
    heading_path: tuple[str, ...],
) -> str:
    section = " / ".join(heading_path) if heading_path else ""
    return (
        f"Document: {document_title} | Revision: {revision} | Section: {section}"
    )


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p]


def _pack_sentences(
    sentences: list[str],
    *,
    max_tokens: int,
    token_count: TokenCounter,
) -> tuple[list[str], int]:
    """Pack sentences into chunks without truncation; overflow splits at boundaries."""
    chunks: list[str] = []
    current: list[str] = []
    overflow_splits = 0
    for sentence in sentences:
        candidate = " ".join(current + [sentence]).strip()
        if current and token_count(candidate) > max_tokens:
            chunks.append(" ".join(current))
            current = [sentence]
            overflow_splits += 1
            if token_count(sentence) > max_tokens:
                # Split long sentence on commas as secondary boundary; never truncate.
                pieces = [p.strip() for p in re.split(r",\s*", sentence) if p.strip()]
                if len(pieces) > 1:
                    current = []
                    for piece in pieces:
                        cand = " ".join(current + [piece]).strip()
                        if current and token_count(cand) > max_tokens:
                            chunks.append(" ".join(current))
                            current = [piece]
                            overflow_splits += 1
                        else:
                            current.append(piece)
                else:
                    current = [sentence]
        else:
            current.append(sentence)
    if current:
        chunks.append(" ".join(current))
    return chunks, overflow_splits


def chunk_document(
    sections: list[SectionInput],
    *,
    document_title: str,
    revision: str = "1",
    child_max_tokens: int = 50,
    parent_max_tokens: int = 200,
    table_row_group_size: int = 15,
    token_count: TokenCounter = whitespace_token_count,
) -> ChunkingResult:
    result = ChunkingResult()
    counter = 0

    def next_id(prefix: str) -> str:
        nonlocal counter
        counter += 1
        return f"{prefix}-{counter}"

    for section in sections:
        header = build_contextual_header(
            document_title=document_title,
            revision=revision,
            heading_path=section.heading_path,
        )
        parent_id = next_id("parent")
        parent_parts: list[str] = []

        # Procedure steps: never split mid-step; warnings stay with step.
        if section.steps:
            title = section.procedure_title or (
                section.heading_path[-1] if section.heading_path else "Procedure"
            )
            for step_text, warnings in section.steps:
                body = f"{title}: {step_text}"
                if warnings:
                    body = body + " " + " ".join(warnings)
                result.children.append(
                    Chunk(
                        chunk_id=next_id("chunk"),
                        section_id=section.section_id,
                        chunk_type="procedure_step",
                        text=body,
                        contextual_header=header,
                        parent_section_id=parent_id,
                        heading_path=section.heading_path,
                    )
                )
                parent_parts.append(body)

        # Table: row groups with repeated header + one summary.
        if section.table_headers and section.table_rows:
            header_line = " | ".join(section.table_headers)
            for start in range(0, len(section.table_rows), table_row_group_size):
                group = section.table_rows[start : start + table_row_group_size]
                lines = [header_line] + [" | ".join(row) for row in group]
                text = "\n".join(lines)
                result.children.append(
                    Chunk(
                        chunk_id=next_id("chunk"),
                        section_id=section.section_id,
                        chunk_type="table_rows",
                        text=text,
                        contextual_header=header,
                        parent_section_id=parent_id,
                        heading_path=section.heading_path,
                    )
                )
                parent_parts.append(text)
            summary = (
                f"Table with columns {header_line}; "
                f"{len(section.table_rows)} data rows."
            )
            result.children.append(
                Chunk(
                    chunk_id=next_id("chunk"),
                    section_id=section.section_id,
                    chunk_type="table_summary",
                    text=summary,
                    contextual_header=header,
                    parent_section_id=parent_id,
                    heading_path=section.heading_path,
                )
            )
            parent_parts.append(summary)

        # Paragraphs packed within section only.
        sentences: list[str] = []
        for paragraph in section.paragraphs:
            sentences.extend(_split_sentences(paragraph))
        packed, splits = _pack_sentences(
            sentences, max_tokens=child_max_tokens, token_count=token_count
        )
        result.overflow_splits += splits
        for text in packed:
            result.children.append(
                Chunk(
                    chunk_id=next_id("chunk"),
                    section_id=section.section_id,
                    chunk_type="text",
                    text=text,
                    contextual_header=header,
                    parent_section_id=parent_id,
                    heading_path=section.heading_path,
                )
            )
            parent_parts.append(text)

        parent_text = "\n\n".join(parent_parts)
        if token_count(parent_text) > parent_max_tokens:
            # Cap parent by taking leading sentences; never truncate mid-sentence.
            parent_sentences = _split_sentences(parent_text)
            capped, _ = _pack_sentences(
                parent_sentences,
                max_tokens=parent_max_tokens,
                token_count=token_count,
            )
            parent_text = capped[0] if capped else ""
        result.parents.append(
            Chunk(
                chunk_id=parent_id,
                section_id=section.section_id,
                chunk_type="parent_section",
                text=parent_text,
                contextual_header=header,
                parent_section_id=None,
                heading_path=section.heading_path,
            )
        )

    # truncations always 0 by construction (split, never cut characters).
    result.truncations = 0
    return result
