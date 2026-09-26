"""
File: test_m2_g3_gate.py
Description: M2 exit gate — Recall@10 within 5 points of G3 (T2.32)
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

from seismobrain_eval.cli import _default_retrieve, _load_golden
from seismobrain_eval.runner import run_evaluation

# G3: Recall@10 ≥ 0.90 / identifier ≥ 0.95. M2: within 5 points → 0.85 / 0.90.
G3_ALL = 0.90
G3_IDENT = 0.95
M2_SLACK = 0.05


def test_m2_within_five_points_of_g3() -> None:
    dataset = _load_golden()
    assert dataset.name == "golden-v0"
    golden_path = (
        Path(__file__).resolve().parents[2] / "datasets" / "golden-v0" / "cases.yaml"
    )
    assert golden_path.exists()
    record = run_evaluation(dataset, retrieve=_default_retrieve)
    assert record.metrics["recall@10"] >= G3_ALL - M2_SLACK
    assert record.metrics.get("identifier", 0.0) >= G3_IDENT - M2_SLACK
