"""Controlled ingestion failure fixture, installed only by create_e2e_app."""

from __future__ import annotations

from collections.abc import Mapping

from fastapi import FastAPI, Request

from seismobrain_api.auth.deps import require_admin
from seismobrain_api.container import AppContainer
from seismobrain_api.starter_ingest import make_ingest_handler
from seismobrain_core.ingestion_jobs import IngestionMonitor
from seismobrain_core.job_execution import ingestion_stage


def install_ingestion_fixture(app: FastAPI, container: AppContainer) -> None:
    recovered: set[str] = set()
    handler = make_ingest_handler(container)

    def controlled_handler(payload: Mapping[str, object]) -> None:
        if (
            str(payload.get("filename", "")).startswith("monitor-recoverable-")
            and str(payload["document_id"]) not in recovered
        ):
            with ingestion_stage("PARSED"):
                raise ValueError("Controlled test failure")
        handler(payload)

    container.job_queue.register("ingest.document", controlled_handler)

    @app.post("/_test/ingestion/{job_id}/restore")
    def restore(job_id: str, request: Request) -> dict[str, bool]:
        require_admin(request)
        monitor = container.job_queue
        assert isinstance(monitor, IngestionMonitor)
        recovered.add(monitor.get_job(job_id).document_id)
        return {"restored": True}
