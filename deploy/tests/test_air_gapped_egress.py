"""
File: test_air_gapped_egress.py
Description: Air-gapped network enforcement and egress self-test (T4.16)
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
import yaml

from seismobrain_api.air_gapped import (
    AirGappedStartupError,
    assert_air_gapped_startup,
    run_egress_self_test,
)

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "compose.yaml"
OVERLAY = ROOT / "compose.air-gapped.yaml"


def test_compose_internal_network_denies_egress() -> None:
    data = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    assert data["networks"]["internal"]["internal"] is True
    for name in ("api", "web", "models", "worker-ingest", "worker-default"):
        nets = data["services"][name]["networks"]
        assert nets == ["internal"] or set(nets) == {"internal"}


def test_air_gapped_overlay_sets_flag() -> None:
    overlay = yaml.safe_load(OVERLAY.read_text(encoding="utf-8"))
    assert overlay["services"]["api"]["environment"]["AIR_GAPPED"] == "true"
    assert overlay["networks"]["internal"]["internal"] is True


def test_air_gapped_startup_requires_passing_self_test() -> None:
    ok = run_egress_self_test(probe=lambda: False)
    assert ok.passed is True
    assert_air_gapped_startup(air_gapped=True, self_test=ok)

    failed = run_egress_self_test(probe=lambda: True)
    assert failed.passed is False
    with pytest.raises(AirGappedStartupError):
        assert_air_gapped_startup(air_gapped=True, self_test=failed)

    # Non-air-gapped startups skip the gate.
    assert_air_gapped_startup(air_gapped=False, self_test=failed)
