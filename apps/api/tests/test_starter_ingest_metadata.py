"""
File: test_starter_ingest_metadata.py
Description: Starter ingest must stamp real per-chunk page numbers, not a hardcoded 1
    (FR-DOC-04)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-18
Modified: 2026-09-19
Version: 0.1.1
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, StreamObject

from seismobrain_adapters.authz.deny import DenyAllAuthorizationGuard
from seismobrain_adapters.event_log.in_memory import InMemoryEventLog
from seismobrain_adapters.metadata.sqlite import SqliteMetadataStore
from seismobrain_adapters.object_store.filesystem import FilesystemObjectStore
from seismobrain_adapters.queue.in_process import InProcessJobQueue
from seismobrain_adapters.rate_limit.in_memory import InMemoryRateLimiter
from seismobrain_api.auth.users import InMemoryUserStore
from seismobrain_api.config import Settings
from seismobrain_api.container import AppContainer
from seismobrain_api.starter_ingest import register_starter_ingest
from seismobrain_core.roles import WorkspaceRole
from seismobrain_ingest.jobs import INGEST_JOB_NAME

_PAGE_ONE_TEXT = (
    "Introduction and scope of the manual overview covers general background context "
    "history purpose objectives audience prerequisites conventions terminology definitions "
    "abbreviations references related documents version control notes summary details today."
)
_PAGE_TWO_TEXT = (
    "Calibration procedure requires the sensor to warm up first before any readings are taken "
    "carefully and technicians must verify accuracy against reference standards documented "
    "thoroughly for every survey conducted across the entire deployment period consistently now."
)


def _two_page_pdf_bytes() -> bytes:
    writer = PdfWriter()
    for text in (_PAGE_ONE_TEXT, _PAGE_TWO_TEXT):
        page = writer.add_blank_page(width=200, height=200)
        stream = StreamObject()
        stream.set_data(f"BT /F1 12 Tf 10 100 Td ({text}) Tj ET".encode())
        stream_ref = writer._add_object(stream)  # noqa: SLF001
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


def test_starter_ingest_stamps_real_page_numbers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    container = AppContainer(
        settings=Settings(),  # type: ignore[call-arg]
        metadata_store=SqliteMetadataStore(tmp_path / "meta.db"),
        job_queue=InProcessJobQueue(tmp_path / "jobs"),
        object_store=FilesystemObjectStore(tmp_path / "objects"),
        event_log=InMemoryEventLog(),
        rate_limiter=InMemoryRateLimiter(),
        authorization_guard=DenyAllAuthorizationGuard(),
        user_store=InMemoryUserStore(),
    )
    register_starter_ingest(container)
    container.collection_access.map_collection("col1", "ws1")
    container.collection_access.set_workspace_role("u1", "ws1", WorkspaceRole.OWNER)
    container.collection_access.grant_write("u1", "col1")

    key = "collections/col1/documents/d1/manual.pdf"
    container.object_store.put(key, _two_page_pdf_bytes())
    job_id = container.job_queue.enqueue(
        INGEST_JOB_NAME,
        {
            "document_id": "d1",
            "collection_id": "col1",
            "object_key": key,
            "filename": "manual.pdf",
        },
    )
    container.job_queue.run_pending(timeout_seconds=5)
    assert container.job_queue.get_status(job_id) == "succeeded"

    page1_hits = container.search_index.query(text="introduction scope overview")
    page2_hits = container.search_index.query(text="calibration procedure warm up")
    assert page1_hits
    assert page2_hits
    assert page1_hits[0].metadata["page"] == 1
    assert page2_hits[0].metadata["page"] == 2


def _pdf_with_heading(heading: str, body: str) -> bytes:
    writer = PdfWriter()
    page = writer.add_blank_page(width=200, height=300)
    stream = StreamObject()
    stream.set_data(
        f"BT /F1 12 Tf 10 200 Td ({heading}) Tj ET\nBT /F1 12 Tf 10 100 Td ({body}) Tj ET".encode()
    )
    stream_ref = writer._add_object(stream)  # noqa: SLF001
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


def test_starter_ingest_stamps_real_section_headings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    container = AppContainer(
        settings=Settings(),  # type: ignore[call-arg]
        metadata_store=SqliteMetadataStore(tmp_path / "meta.db"),
        job_queue=InProcessJobQueue(tmp_path / "jobs"),
        object_store=FilesystemObjectStore(tmp_path / "objects"),
        event_log=InMemoryEventLog(),
        rate_limiter=InMemoryRateLimiter(),
        authorization_guard=DenyAllAuthorizationGuard(),
        user_store=InMemoryUserStore(),
    )
    register_starter_ingest(container)
    container.collection_access.map_collection("col1", "ws1")
    container.collection_access.set_workspace_role("u1", "ws1", WorkspaceRole.OWNER)
    container.collection_access.grant_write("u1", "col1")

    body = (
        "The Section Editor is used to insert or delete and renumber section markers "
        "and is started from the OpsConsole QC desktop application."
    )
    key = "collections/col1/documents/d2/ch03.pdf"
    container.object_store.put(key, _pdf_with_heading("1.3 Section Editor", body))
    job_id = container.job_queue.enqueue(
        INGEST_JOB_NAME,
        {
            "document_id": "d2",
            "collection_id": "col1",
            "object_key": key,
            "filename": "ch03.pdf",
        },
    )
    container.job_queue.run_pending(timeout_seconds=5)
    assert container.job_queue.get_status(job_id) == "succeeded"

    hits = container.search_index.query(text="section editor insert delete renumber")
    assert hits
    assert hits[0].metadata["section_path"] == "1.3 Section Editor"
