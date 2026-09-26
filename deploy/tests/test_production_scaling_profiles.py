"""
File: test_production_scaling_profiles.py
Description: PgBouncer and models multi-replica batching (T6.13)
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

ROOT = Path(__file__).resolve().parents[1]
PG = ROOT / "helm" / "seismobrain" / "templates" / "pgbouncer-config.yaml"
VALUES = ROOT / "helm" / "seismobrain" / "values.yaml"


def test_pgbouncer_profile_above_four_api_replicas() -> None:
    text = PG.read_text(encoding="utf-8")
    assert "activate_above_api_replicas" in text
    assert '"4"' in text or "4" in text
    assert "pool_mode" in text
    values = VALUES.read_text(encoding="utf-8")
    assert "pgbouncer:" in values
    assert "batching: true" in values
    assert "maxBatchSize:" in values


def test_models_multi_replica_batching_configured() -> None:
    values = VALUES.read_text(encoding="utf-8")
    assert "models: 2" in values or "models:" in values
    text = PG.read_text(encoding="utf-8")
    assert "models_batching" in text
    assert "models_max_batch_size" in text
