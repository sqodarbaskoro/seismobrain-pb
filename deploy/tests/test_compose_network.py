"""
File: test_compose_network.py
Description: TLS edge and private internal network checks (SEC-01 / T0c.2)
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

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "compose.yaml"
CADDY = ROOT / "proxy" / "Caddyfile"


def _load_compose() -> dict[str, Any]:
    data = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_only_proxy_publishes_ports() -> None:
    services = _load_compose()["services"]
    for name, svc in services.items():
        ports = svc.get("ports") or []
        if name == "proxy":
            assert ports, "proxy must publish ports"
        else:
            assert not ports, f"{name} must not publish ports"


def test_internal_network_is_private() -> None:
    networks = _load_compose()["networks"]
    assert networks["internal"]["internal"] is True
    proxy = _load_compose()["services"]["proxy"]
    assert "edge" in proxy["networks"]
    assert "internal" in proxy["networks"]
    for name in ("postgres", "redis", "qdrant", "api", "web"):
        nets = _load_compose()["services"][name]["networks"]
        assert nets == ["internal"] or set(nets) == {"internal"}


def test_caddyfile_enables_tls_and_hsts() -> None:
    text = CADDY.read_text(encoding="utf-8")
    assert "Strict-Transport-Security" in text
    assert "tls" in text.lower() or "https://" in text or "{env.SB_DOMAIN}" in text
