"""
File: gate_calibration.py
Description: Workspace answerability gate calibration policy (FR-EVAL-07)
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

from dataclasses import dataclass

RETRAIN_MIN_CASES = 500


@dataclass(frozen=True, slots=True)
class WorkspaceGateState:
    workspace_id: str
    calibrated: bool
    labelled_cases: int
    positive_cases: int = 0
    negative_cases: int = 0
    threshold: float | None = None

    @property
    def ui_marking(self) -> str:
        return "calibrated" if self.calibrated else "uncalibrated"


def may_retrain_workspace_gate(state: WorkspaceGateState) -> bool:
    """Workspace retraining only after ≥500 balanced labelled cases."""
    if state.labelled_cases < RETRAIN_MIN_CASES:
        return False
    if state.positive_cases < RETRAIN_MIN_CASES // 2:
        return False
    if state.negative_cases < RETRAIN_MIN_CASES // 2:
        return False
    return True
