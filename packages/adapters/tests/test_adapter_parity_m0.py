"""
File: test_adapter_parity_m0.py
Description: Starter vs Team adapter parity for MetadataStore, EventLog, JobQueue, ObjectStore
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-26
Version: 0.2.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from testcontainers.community.minio import MinioContainer
from testcontainers.community.postgres import PostgresContainer
from testcontainers.community.redis import RedisContainer

from seismobrain_adapters.event_log.in_memory import InMemoryEventLog
from seismobrain_adapters.event_log.redis_streams import RedisStreamsEventLog
from seismobrain_adapters.metadata.postgres import PostgresMetadataStore
from seismobrain_adapters.metadata.sqlite import SqliteMetadataStore
from seismobrain_adapters.object_store.filesystem import FilesystemObjectStore
from seismobrain_adapters.object_store.s3 import S3ObjectStore
from seismobrain_adapters.queue.dramatiq_redis import DramatiqRedisJobQueue
from seismobrain_adapters.queue.in_process import InProcessJobQueue
from seismobrain_core.ports import EventLog, JobQueue, MetadataStore, ObjectStore

_POSTGRES_IMAGE = "postgres:16.10-alpine"
_REDIS_IMAGE = "redis:7.4.2-alpine"


def _assert_metadata(store: MetadataStore) -> None:
    assert store.count_tenants() == 0
    tenant = store.create_tenant("ParityCo")
    assert store.get_tenant(tenant.id) == tenant
    assert store.count_tenants() == 1


def _assert_event_log(log: EventLog) -> None:
    stream = "parity:stream"
    first = log.append(stream, {"n": 1})
    second = log.append(stream, {"n": 2})
    assert [e.event_id for e in log.replay(stream, after_id=first)] == [second]


def _assert_job_queue(queue: JobQueue) -> None:
    seen: list[int] = []

    def handler(payload: dict[str, object]) -> None:
        seen.append(int(str(payload["v"])))

    queue.register("n", handler)
    job_id = queue.enqueue("n", {"v": 7})
    queue.run_pending(timeout_seconds=5.0)
    assert seen == [7]
    assert queue.get_status(job_id) == "succeeded"


def _assert_object_store(store: ObjectStore) -> None:
    store.put("parity/a.bin", b"abc")
    assert store.get("parity/a.bin") == b"abc"
    assert store.exists("parity/a.bin")
    store.delete("parity/a.bin")
    assert not store.exists("parity/a.bin")


@pytest.fixture(scope="module")
def postgres_url() -> Iterator[str]:
    with PostgresContainer(_POSTGRES_IMAGE) as container:
        yield container.get_connection_url()


@pytest.fixture(scope="module")
def redis_url() -> Iterator[str]:
    with RedisContainer(_REDIS_IMAGE) as container:
        host = container.get_container_host_ip()
        port = container.get_exposed_port(container.port)
        yield f"redis://{host}:{port}/0"


@pytest.fixture(scope="module")
def minio_store(minio_container: MinioContainer) -> Iterator[S3ObjectStore]:
    cfg = minio_container.get_config()
    store = S3ObjectStore(
        endpoint_url=f"http://{cfg['endpoint']}",
        access_key=str(cfg["access_key"]),
        secret_key=str(cfg["secret_key"]),
        bucket="parity",
    )
    store.ensure_bucket()
    yield store


def test_metadata_store_parity_starter_vs_team(tmp_path: Path, postgres_url: str) -> None:
    starter = SqliteMetadataStore(tmp_path / "meta.db")
    team = PostgresMetadataStore(postgres_url)
    team.reset_schema()
    _assert_metadata(starter)
    _assert_metadata(team)


def test_event_log_parity_starter_vs_team(redis_url: str) -> None:
    starter: EventLog = InMemoryEventLog(capacity=32)
    team = RedisStreamsEventLog(redis_url)
    try:
        _assert_event_log(starter)
        _assert_event_log(team)
    finally:
        team.close()


def test_job_queue_parity_starter_vs_team(tmp_path: Path, redis_url: str) -> None:
    starter: JobQueue = InProcessJobQueue(tmp_path / "jobs")
    team = DramatiqRedisJobQueue(redis_url, database_url=f"sqlite:///{tmp_path / 'team-jobs.db'}")
    try:
        _assert_job_queue(starter)
        _assert_job_queue(team)
    finally:
        team.close()


def test_object_store_parity_starter_vs_team(tmp_path: Path, minio_store: S3ObjectStore) -> None:
    starter: ObjectStore = FilesystemObjectStore(tmp_path / "objects")
    _assert_object_store(starter)
    _assert_object_store(minio_store)
