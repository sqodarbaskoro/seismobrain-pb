"""
File: test_starter_restart_persistence.py
Description: Uploaded documents and their retrieval index survive a Starter restart
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-18
Modified: 2026-09-18
Version: 0.1.0
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
from seismobrain_api.collection_access import InMemoryCollectionAccessStore
from seismobrain_api.config import Settings
from seismobrain_api.container import AppContainer
from seismobrain_api.search_index import InMemorySearchIndex
from seismobrain_api.starter_ingest import register_starter_ingest
from seismobrain_core.roles import WorkspaceRole
from seismobrain_ingest.jobs import INGEST_JOB_NAME


def _build_container(root: Path) -> AppContainer:
    """Mirrors build_starter_app's wiring against a shared data dir."""
    container = AppContainer(
        settings=Settings(),  # type: ignore[call-arg]
        metadata_store=SqliteMetadataStore(root / "meta.db"),
        job_queue=InProcessJobQueue(root / "jobs"),
        object_store=FilesystemObjectStore(root / "objects"),
        event_log=InMemoryEventLog(),
        rate_limiter=InMemoryRateLimiter(),
        authorization_guard=DenyAllAuthorizationGuard(),
        user_store=InMemoryUserStore(),
        collection_access=InMemoryCollectionAccessStore(db_path=root / "documents.db"),
        search_index=InMemorySearchIndex(db_path=root / "search_index.db"),
    )
    register_starter_ingest(container)
    return container


def test_uploaded_document_survives_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)

    before = _build_container(tmp_path)
    before.collection_access.map_collection("col1", "ws1")
    before.collection_access.set_workspace_role("u1", "ws1", WorkspaceRole.OWNER)
    before.collection_access.grant_write("u1", "col1")

    key = "collections/col1/documents/d1/note.md"
    before.object_store.put(key, b"# Flange\n\nTorque for flange P2/94 is 40 Nm.\n")
    before.job_queue.enqueue(
        INGEST_JOB_NAME,
        {
            "document_id": "d1",
            "collection_id": "col1",
            "object_key": key,
            "filename": "note.md",
        },
    )
    before.job_queue.run_pending(timeout_seconds=5)
    assert before.collection_access.get_document("d1") is not None
    assert before.search_index.query(text="torque flange")

    # Simulate a process restart: fresh in-memory stores, same data dir, no re-upload.
    # ACL grants are rebuilt from catalog.db by hydrate_collection_access() in the real
    # app (already covered elsewhere); reproduce that step here so this test isolates
    # what T7.29 actually fixes — documents and chunks, not grants.
    after = _build_container(tmp_path)
    after.collection_access.map_collection("col1", "ws1")
    after.collection_access.set_workspace_role("u1", "ws1", WorkspaceRole.OWNER)
    after.collection_access.grant_write("u1", "col1")

    docs = after.collection_access.list_documents("u1", "col1")
    assert [d["id"] for d in docs] == ["d1"]

    hits = after.search_index.query(text="torque flange")
    assert hits
    assert "40 Nm" in hits[0].text
