"""
File: test_gate_calibration_hierarchy.py
Description: Workspace gate threshold calibration hierarchy (T5.9)
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

from seismobrain_core.gate_calibration import (
    RETRAIN_MIN_CASES,
    WorkspaceGateState,
    may_retrain_workspace_gate,
)


def test_retrain_requires_500_balanced_and_uncalibrated_flag() -> None:
    uncal = WorkspaceGateState(workspace_id="w1", calibrated=False, labelled_cases=10)
    assert uncal.ui_marking == "uncalibrated"
    assert may_retrain_workspace_gate(uncal) is False
    ready = WorkspaceGateState(
        workspace_id="w1",
        calibrated=True,
        labelled_cases=RETRAIN_MIN_CASES,
        positive_cases=250,
        negative_cases=250,
    )
    assert may_retrain_workspace_gate(ready) is True
    assert RETRAIN_MIN_CASES == 500
