"""
File: test_admin_ingestion_monitor.py
Description: Ingestion monitor queue stages failures retry (T3.23)
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


@pytest.fixture
def container(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AppContainer:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    monkeypatch.setenv("SB_TIER", "starter")
    return AppContainer(
        settings=Settings(),  # type: ignore[call-arg]
        metadata_store=SqliteMetadataStore(tmp_path / "meta.db"),
        job_queue=InProcessJobQueue(tmp_path / "jobs"),
        object_store=FilesystemObjectStore(tmp_path / "objects"),
        event_log=InMemoryEventLog(),
        rate_limiter=InMemoryRateLimiter(),
        authorization_guard=DenyAllAuthorizationGuard(),
        user_store=InMemoryUserStore(),
    )


HEADERS = {"X-System-Role": "system_admin"}
BASE = "/api/v1/admin/ingestion"


def test_ingestion_monitor_and_retry(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    assert client.get(f"{BASE}/monitor").status_code in {401, 403}
    queue = container.job_queue
    assert isinstance(queue, InProcessJobQueue)
    queue.store.retry_delay = 0
    job_id = queue.enqueue("ingest.document", {"filename": "guide.md", "collection_id": "c"})
    assert client.get(f"{BASE}/monitor", headers=HEADERS).json()["queue_depth"] == 1
    queue.run_pending()  # Missing handler must become an actual failure.
    body = client.get(f"{BASE}/monitor", headers=HEADERS).json()
    assert body["queue_depth"] == 0
    assert body["dead_letter"] == 1
    assert client.post(f"{BASE}/jobs/missing/retry", headers=HEADERS).status_code == 404
    retry = client.post(f"{BASE}/jobs/{job_id}/retry", headers=HEADERS)
    assert retry.json()["status"] == "pending"
    assert client.post(f"{BASE}/jobs/{job_id}/retry", headers=HEADERS).status_code == 409
    seen: list[object] = []
    queue.register("ingest.document", lambda payload: seen.append(payload["filename"]))
    queue.run_pending()
    assert seen == ["guide.md"]
    assert queue.get_status(job_id) == "succeeded"
    page = client.get(f"{BASE}/jobs?status=succeeded&search=guide&limit=1", headers=HEADERS).json()
    assert page["total"] == 1
    assert page["jobs"][0]["id"] == job_id
    assert page["jobs"][0]["events"] == []
    detail = client.get(f"{BASE}/jobs/{job_id}", headers=HEADERS).json()
    assert any(event["status"] == "retry" for event in detail["events"])
    assert client.get(f"{BASE}/jobs?limit=0", headers=HEADERS).status_code == 422


def test_quarantine_release_and_authorization(container: AppContainer) -> None:
    client = TestClient(create_app(container))
    job_id = container.job_queue.enqueue("ingest.document", {"filename": "guide.md"})
    for suffix in ["", "/retry", "/quarantine", "/release"]:
        path = f"{BASE}/jobs/{job_id}{suffix}"
        response = (
            client.post(path, json={"reason": "Review source"}) if suffix else client.get(path)
        )
        assert response.status_code in {401, 403}
    response = client.post(
        f"{BASE}/jobs/{job_id}/quarantine", headers=HEADERS, json={"reason": "Review source"}
    )
    assert response.json()["status"] == "quarantined"
    container.job_queue.run_pending()
    assert container.job_queue.get_status(job_id) == "quarantined"
    assert client.post(f"{BASE}/jobs/{job_id}/retry", headers=HEADERS).status_code == 409
    assert (
        client.post(f"{BASE}/jobs/{job_id}/release", headers=HEADERS).json()["status"] == "pending"
    )


def test_storage_failure_is_not_healthy_zero(
    container: AppContainer, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sqlalchemy.exc import OperationalError

    def unavailable() -> None:
        raise OperationalError("unavailable", {}, Exception())

    monkeypatch.setattr(container.job_queue, "summary", unavailable)
    client = TestClient(create_app(container))
    assert client.get(f"{BASE}/monitor", headers=HEADERS).status_code == 503
