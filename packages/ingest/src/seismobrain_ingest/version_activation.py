"""
File: version_activation.py
Description: Document version activation protocol §8.1.1 / DR-18 (FR-DOC-04)
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

from dataclasses import dataclass, field
from typing import Literal

ActivationStep = Literal[0, 1, 2, 3, 4, 5]


@dataclass(slots=True)
class VectorPointState:
    point_id: str
    version_id: str
    is_latest: bool
    verified: bool = False


@dataclass
class ActivationStore:
    """In-memory metadata + vector state for activation protocol tests."""

    current_version_id: dict[str, str] = field(default_factory=dict)
    points: dict[str, list[VectorPointState]] = field(default_factory=dict)
    activation_step: dict[str, ActivationStep] = field(default_factory=dict)
    audit: list[str] = field(default_factory=list)

    def set_current(self, document_id: str, version_id: str) -> None:
        self.current_version_id[document_id] = version_id

    def query_visible_versions(self, document_id: str) -> list[str]:
        """Simulate retrieval + version guard: only current_version_id survives."""
        current = self.current_version_id.get(document_id)
        if current is None:
            return []
        # Unverified new points never become current; guard filters to current only.
        return [current]


def activate_version(
    store: ActivationStore,
    *,
    document_id: str,
    old_version_id: str,
    new_version_id: str,
    new_point_ids: list[str],
    start_from: ActivationStep = 0,
) -> ActivationStep:
    """Run activation steps 1–5; resume from start_from when interrupted."""
    step: ActivationStep = start_from
    store.activation_step[document_id] = step

    if step < 1:
        # Step 1: write new points is_latest=false; mark verified.
        points = store.points.setdefault(document_id, [])
        for pid in new_point_ids:
            points.append(
                VectorPointState(
                    point_id=pid,
                    version_id=new_version_id,
                    is_latest=False,
                    verified=True,
                )
            )
        step = 1
        store.activation_step[document_id] = step

    if step < 2:
        # Step 2: set is_latest=true on new points.
        for point in store.points.get(document_id, []):
            if point.version_id == new_version_id:
                point.is_latest = True
        step = 2
        store.activation_step[document_id] = step

    if step < 3:
        # Step 3: metadata current_version_id = new.
        store.set_current(document_id, new_version_id)
        step = 3
        store.activation_step[document_id] = step

    if step < 4:
        # Step 4: set is_latest=false on old points.
        for point in store.points.get(document_id, []):
            if point.version_id == old_version_id:
                point.is_latest = False
        step = 4
        store.activation_step[document_id] = step

    if step < 5:
        store.audit.append(f"activated:{document_id}:{new_version_id}")
        step = 5
        store.activation_step[document_id] = step

    return step


def reconcile_activation(
    store: ActivationStore,
    *,
    document_id: str,
    old_version_id: str,
    new_version_id: str,
    new_point_ids: list[str],
) -> ActivationStep:
    """Resume interrupted activation from the recorded step."""
    recorded = store.activation_step.get(document_id, 0)
    return activate_version(
        store,
        document_id=document_id,
        old_version_id=old_version_id,
        new_version_id=new_version_id,
        new_point_ids=new_point_ids,
        start_from=recorded,
    )
