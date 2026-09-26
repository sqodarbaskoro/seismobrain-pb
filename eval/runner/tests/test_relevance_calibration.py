"""
File: test_relevance_calibration.py
Description: Passage-relevance calibration artifact tests (T2.19)
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

import json
from pathlib import Path

from seismobrain_eval.calibration import calibrate_relevance, write_artifact


def test_calibrate_relevance_produces_versioned_artifact(tmp_path: Path) -> None:
    pairs = [(0.2, 0.1), (0.8, 0.9), (0.5, 0.55)]
    artifact = calibrate_relevance(pairs, version="rel-cal-v1")
    assert artifact.kind == "relevance"
    assert artifact.version == "rel-cal-v1"
    assert "mae" in artifact.metrics
    assert "scale" in artifact.mapping
    out = tmp_path / "rel-cal-v1.json"
    write_artifact(artifact, out)
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["version"] == "rel-cal-v1"
    assert loaded["metrics"]["n"] == 3.0
