"""
File: test_starter_ingest.py
Description: Starter ingest handler indexes uploaded text for retrieval
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-17
Modified: 2026-09-19
Version: 0.2.1
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from pathlib import Path

import pytest

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


def test_starter_ingest_indexes_markdown(
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

    key = "collections/col1/documents/d1/note.md"
    container.object_store.put(
        key, b"# Flange\n\nTorque for flange P2/94 is 40 Nm.\n"
    )
    job_id = container.job_queue.enqueue(
        INGEST_JOB_NAME,
        {
            "document_id": "d1",
            "collection_id": "col1",
            "object_key": key,
            "filename": "note.md",
        },
    )
    container.job_queue.run_pending(timeout_seconds=5)
    assert container.job_queue.get_status(job_id) == "succeeded"
    hits = container.search_index.query(text="torque flange")
    assert hits
    assert "40 Nm" in hits[0].text


def test_chunk_ids_are_unique_across_documents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """chunk_document() numbers chunks "chunk-1", "chunk-2", ... starting fresh on
    every call (one call per ingested document), so two documents can otherwise
    produce colliding chunk_ids in the shared search index — silently merging two
    unrelated chunks under one id wherever chunk_id is used as a lookup key."""
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

    for doc_id in ("d1", "d2"):
        key = f"collections/col1/documents/{doc_id}/note.md"
        container.object_store.put(key, f"Body text for {doc_id}.".encode())
        job_id = container.job_queue.enqueue(
            INGEST_JOB_NAME,
            {
                "document_id": doc_id,
                "collection_id": "col1",
                "object_key": key,
                "filename": "note.md",
            },
        )
        container.job_queue.run_pending(timeout_seconds=5)
        assert container.job_queue.get_status(job_id) == "succeeded"

    hits = container.search_index.query(text="body text", collection_ids=["col1"])
    chunk_ids = [h.metadata["chunk_id"] for h in hits]
    assert len(chunk_ids) == len(set(chunk_ids)), f"colliding chunk_ids: {chunk_ids}"


def test_starter_ingest_extracts_real_pdf_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A real (non-fixture) PDF must be indexed with its actual extracted text,
    not a best-effort byte decode of the binary PDF stream."""
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

    fixture = (
        Path(__file__).parent.parent.parent.parent
        / "packages/ingest/tests/fixtures/device_controller_real.pdf"
    )
    key = "collections/col1/documents/d2/device_controller.pdf"
    container.object_store.put(key, fixture.read_bytes())
    job_id = container.job_queue.enqueue(
        INGEST_JOB_NAME,
        {
            "document_id": "d2",
            "collection_id": "col1",
            "object_key": key,
            "filename": "device_controller.pdf",
        },
    )
    container.job_queue.run_pending(timeout_seconds=5)
    assert container.job_queue.get_status(job_id) == "succeeded"
    hits = container.search_index.query(text="sensor volt levels")
    assert hits
    assert "Device Controller monitors sensor volt levels." in hits[0].text
