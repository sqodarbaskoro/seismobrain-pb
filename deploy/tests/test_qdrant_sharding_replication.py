"""
File: test_qdrant_sharding_replication.py
Description: Qdrant sharding/replication without app changes (T6.4)
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
CFG = ROOT / "helm" / "seismobrain" / "templates" / "qdrant-config.yaml"
VALUES = ROOT / "helm" / "seismobrain" / "values.yaml"
DOC = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "operations"
    / "qdrant-sharding.md"
)


def test_helm_exposes_shards_and_replication() -> None:
    values = VALUES.read_text(encoding="utf-8")
    assert "shards:" in values
    assert "replicationFactor:" in values
    cfg = CFG.read_text(encoding="utf-8")
    assert "shard-agnostic" in cfg or "Application code is shard-agnostic" in cfg
    assert "replication_factor" in cfg


def test_sharding_documented() -> None:
    assert DOC.is_file()
    text = DOC.read_text(encoding="utf-8")
    assert "without application changes" in text.lower()
    assert "replication" in text.lower()
