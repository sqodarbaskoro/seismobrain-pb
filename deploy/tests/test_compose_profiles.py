"""
File: test_compose_profiles.py
Description: Compose infra/core profiles, healthchecks, and digest pins (T0c.1)
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

import re
from pathlib import Path
from typing import Any

import yaml

COMPOSE = Path(__file__).resolve().parents[1] / "compose.yaml"
_DIGEST = re.compile(r".+@sha256:[0-9a-f]{64}$")
_LATEST = re.compile(r":latest(@|$)")


def _load() -> dict[str, Any]:
    assert COMPOSE.is_file(), f"missing {COMPOSE}"
    data = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_infra_and_core_profiles_present() -> None:
    services = _load()["services"]
    infra = {"postgres", "redis", "qdrant"}
    core_apps = {"migrate", "api", "models", "worker-ingest", "worker-default", "web", "proxy"}
    for name in infra:
        profiles = set(services[name].get("profiles", []))
        assert profiles == {"infra", "core"}
    for name in core_apps:
        profiles = set(services[name].get("profiles", []))
        assert profiles == {"core"}


def test_every_service_has_healthcheck_and_no_latest() -> None:
    services = _load()["services"]
    for name, svc in services.items():
        assert "healthcheck" in svc, f"{name} missing healthcheck"
        image = svc.get("image", "")
        assert image, f"{name} missing image"
        assert _DIGEST.match(image), f"{name} image not pinned by digest: {image}"
        assert not _LATEST.search(image), f"{name} uses latest: {image}"


def test_dependents_use_service_healthy() -> None:
    services = _load()["services"]
    api_deps = services["api"]["depends_on"]
    assert api_deps["migrate"]["condition"] == "service_completed_successfully"
    assert api_deps["redis"]["condition"] == "service_healthy"
    assert api_deps["models"]["condition"] == "service_healthy"
    migrate_deps = services["migrate"]["depends_on"]
    assert migrate_deps["postgres"]["condition"] == "service_healthy"
    assert migrate_deps["qdrant"]["condition"] == "service_healthy"
