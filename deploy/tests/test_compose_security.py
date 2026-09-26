"""
File: test_compose_security.py
Description: Container non-root read-only no-new-privileges checks (SEC-18 / T0c.3)
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
from typing import Any

import yaml

COMPOSE = Path(__file__).resolve().parents[1] / "compose.yaml"


def _load() -> dict[str, Any]:
    data = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_app_services_are_hardened() -> None:
    services = _load()["services"]
    hardened = ("api", "models", "worker-ingest", "worker-default", "migrate", "web")
    for name in hardened:
        svc = services[name]
        assert svc.get("read_only") is True, name
        assert "no-new-privileges:true" in (svc.get("security_opt") or []), name
        assert "ALL" in (svc.get("cap_drop") or []), name
