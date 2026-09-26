"""
File: health.py
Description: Liveness and readiness health routes (NFR-REL-06)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-16
Version: 0.2.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Request

from seismobrain_api.container import AppContainer
from seismobrain_contracts import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/ready")
def ready(request: Request) -> dict[str, object]:
    container = cast(AppContainer, request.app.state.container)
    checks = {
        "metadata_store": "ok" if container.metadata_store is not None else "fail",
        "queue": "ok" if container.job_queue is not None else "fail",
        # Vector alias and models service are stubbed healthy in M0b until adapters land.
        "vector_alias": "ok",
        "models_service": "ok",
    }
    status = "ready" if all(value == "ok" for value in checks.values()) else "not_ready"
    return {"status": status, "checks": checks}
