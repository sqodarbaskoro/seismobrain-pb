"""
File: test_export_markdown_pdf.py
Description: Export Markdown and PDF with citations (T4.24)
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

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from seismobrain_adapters.authz.deny import DenyAllAuthorizationGuard
from seismobrain_adapters.event_log.in_memory import InMemoryEventLog
from seismobrain_adapters.metadata.sqlite import SqliteMetadataStore
from seismobrain_adapters.object_store.filesystem import FilesystemObjectStore
from seismobrain_adapters.queue.in_process import InProcessJobQueue
from seismobrain_adapters.rate_limit.in_memory import InMemoryRateLimiter
from seismobrain_api.app import create_app
from seismobrain_api.auth.users import InMemoryUserStore
from seismobrain_api.config import Settings
from seismobrain_api.container import AppContainer
from seismobrain_api.conversations import MessageRecord


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    monkeypatch.setenv("SB_TIER", "starter")
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
    app = create_app(container)
    client = TestClient(app)
    created = client.post(
        "/api/v1/conversations",
        headers={"X-User-Id": "u1"},
        json={"workspace_id": "w1", "title": "Export"},
    )
    conv_id = created.json()["id"]
    msg = MessageRecord(
        id=container.conversations.new_message_id(),
        conversation_id=conv_id,
        role="assistant",
        content="Limit is 6 knots [E1].",
        answer=[
            {"text": "Limit is 6 knots [E1].", "evidence_ids": ["E1"]},
        ],
        citations={
            "E1": {
                "title": "Ops Manual",
                "section_path": "3.1",
                "page": 12,
                "table_ref": None,
                "extraction_method": "digital",
            }
        },
    )
    container.conversations.add_message(conv_id, "u1", msg)
    client.conv_id = conv_id  # type: ignore[attr-defined]
    client.msg_id = msg.id  # type: ignore[attr-defined]
    return client


def test_export_markdown_and_pdf_include_citations(client: TestClient) -> None:
    md = client.get(
        f"/api/v1/conversations/{client.conv_id}/messages/{client.msg_id}/export",  # type: ignore[attr-defined]
        headers={"X-User-Id": "u1"},
        params={"format": "markdown"},
    )
    assert md.status_code == 200
    assert "Citations" in md.text
    assert "Ops Manual" in md.text
    assert "[E1]" in md.text

    pdf = client.get(
        f"/api/v1/conversations/{client.conv_id}/messages/{client.msg_id}/export",  # type: ignore[attr-defined]
        headers={"X-User-Id": "u1"},
        params={"format": "pdf"},
    )
    assert pdf.status_code == 200
    assert pdf.headers["content-type"].startswith("application/pdf")
    assert pdf.content.startswith(b"%PDF")
    assert b"Citations" in pdf.content or b"Ops" in pdf.content
