"""
File: test_health_contract.py
Description: Tests for shared health/ready API contracts
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

import pytest
from pydantic import ValidationError

from seismobrain_contracts.health import HealthResponse, ReadyResponse


def test_health_response_ok() -> None:
    model = HealthResponse(status="ok")
    assert model.status == "ok"
    assert model.model_dump() == {"status": "ok"}


def test_ready_response_requires_checks() -> None:
    model = ReadyResponse(
        status="ready",
        checks={"metadata_store": True, "queue": True, "vector_alias": True},
    )
    assert model.status == "ready"
    assert model.checks["metadata_store"] is True


def test_ready_response_rejects_empty_status() -> None:
    with pytest.raises(ValidationError):
        ReadyResponse(status="", checks={})
