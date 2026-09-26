"""
File: test_job_queue.py
Description: JobQueue port tests: in-process Starter and Dramatiq+Redis Team
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

from collections.abc import Iterator
from pathlib import Path

import pytest
from testcontainers.community.redis import RedisContainer

from seismobrain_adapters.queue.dramatiq_redis import DramatiqRedisJobQueue
from seismobrain_adapters.queue.in_process import InProcessJobQueue
from seismobrain_core.ports import JobQueue

# Pin Redis ≥ 7 per PRD; never use :latest.
_REDIS_IMAGE = "redis:7.4.2-alpine"


def _assert_queue_runs_job(queue: JobQueue) -> None:
    seen: list[str] = []

    def handler(payload: dict[str, object]) -> None:
        seen.append(str(payload["value"]))

    queue.register("echo", handler)
    job_id = queue.enqueue("echo", {"value": "hello"})
    assert job_id
    queue.run_pending(timeout_seconds=5.0)
    assert seen == ["hello"]
    assert queue.get_status(job_id) == "succeeded"


def test_in_process_queue_satisfies_port(tmp_path: Path) -> None:
    queue: JobQueue = InProcessJobQueue(tmp_path / "jobs")
    _assert_queue_runs_job(queue)


def test_in_process_queue_persists_across_instances(tmp_path: Path) -> None:
    path = tmp_path / "jobs"
    first = InProcessJobQueue(path)
    first.register("noop", lambda payload: None)
    job_id = first.enqueue("noop", {"n": 1})
    # Do not run; reopen and process from disk.
    second = InProcessJobQueue(path)
    second.register("noop", lambda payload: None)
    assert second.get_status(job_id) == "pending"
    second.run_pending(timeout_seconds=5.0)
    assert second.get_status(job_id) == "succeeded"


@pytest.fixture(scope="module")
def redis_url() -> Iterator[str]:
    with RedisContainer(_REDIS_IMAGE) as container:
        host = container.get_container_host_ip()
        port = container.get_exposed_port(container.port)
        yield f"redis://{host}:{port}/0"


def test_dramatiq_redis_queue_satisfies_port(redis_url: str, tmp_path: Path) -> None:
    queue: JobQueue = DramatiqRedisJobQueue(
        redis_url, database_url=f"sqlite:///{tmp_path / 'team-jobs.db'}"
    )
    try:
        _assert_queue_runs_job(queue)
    finally:
        queue.close()
