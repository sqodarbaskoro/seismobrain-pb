from collections.abc import Iterator
from pathlib import Path

import pytest
from testcontainers.community.postgres import PostgresContainer
from testcontainers.community.redis import RedisContainer

from seismobrain_adapters.metadata.migrations import upgrade_head
from seismobrain_adapters.queue.dramatiq_redis import DramatiqRedisJobQueue
from seismobrain_adapters.queue.job_store import SqlJobStore
from seismobrain_core.job_execution import ingestion_stage


@pytest.fixture(scope="module")
def postgres_url() -> Iterator[str]:
    with PostgresContainer("postgres:16.10-alpine", driver="psycopg") as container:
        yield container.get_connection_url()


@pytest.mark.parametrize("backend", ["sqlite", "postgres"])
def test_durable_store_parity(backend: str, tmp_path: Path, postgres_url: str) -> None:
    url = postgres_url if backend == "postgres" else f"sqlite:///{tmp_path / 'jobs.db'}"
    upgrade_head(url)
    first = SqlJobStore(url, retry_delay=0)
    job = first.enqueue("ingest.document", {"filename": "guide.md", "collection_id": backend})
    second = SqlJobStore(url, retry_delay=0)
    assert second.get(job.id).status == "pending"
    for _ in range(3):
        claim = first.claim(job.id)
        assert claim is not None
        assert second.claim(job.id) is None
        with first.stage(job.id, claim.owner, "PARSED") as counts:
            counts["pages"] = 2
        first.finish(job.id, claim.owner, error="Index unavailable")
    assert second.get(job.id).status == "dead_letter"
    assert second.get(job.id).checkpoints["PARSED"]["pages"] == 2
    second.action(job.id, "retry", actor="admin")
    assert first.get(job.id).status == "pending"
    assert first.page(collection_id=backend).total >= 1


def _team_worker(redis_url: str, database_url: str) -> None:
    worker = DramatiqRedisJobQueue(redis_url, database_url=database_url)

    def handler(payload: dict[str, object]) -> None:
        with ingestion_stage("PARSED") as counts:
            counts["pages"] = 1

    worker.register("ingest.document", handler)
    try:
        worker.run_pending(10)
    finally:
        worker.close()


def test_postgres_redis_delivery_and_status_shared_between_processes(postgres_url: str) -> None:
    import multiprocessing

    with RedisContainer("redis:7.4.2-alpine") as redis:
        url = f"redis://{redis.get_container_host_ip()}:{redis.get_exposed_port(6379)}/0"
        api = DramatiqRedisJobQueue(url, database_url=postgres_url)
        try:
            job_id = api.enqueue("ingest.document", {"filename": "team.md"})
            # API never sends a broker message; a separate worker repairs dispatch from SQL.
            process = multiprocessing.get_context("spawn").Process(
                target=_team_worker,
                args=(url, postgres_url),
            )
            process.start()
            process.join(20)
            if process.is_alive():
                process.terminate()
                process.join()
                raise AssertionError("Team worker did not finish")
            assert process.exitcode == 0
            assert api.get_status(job_id) == "succeeded"
            assert api.get_job(job_id).checkpoints == {"PARSED": {"pages": 1}}
        finally:
            api.close()
