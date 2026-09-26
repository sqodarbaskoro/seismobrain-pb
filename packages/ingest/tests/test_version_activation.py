"""
File: test_version_activation.py
Description: FR-DOC-04 — version activation protocol §8.1.1
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

from seismobrain_ingest.version_activation import (
    ActivationStore,
    VectorPointState,
    activate_version,
    reconcile_activation,
)


def _seed_old(store: ActivationStore) -> None:
    store.set_current("doc-1", "v1")
    store.points["doc-1"] = [
        VectorPointState(
            point_id="p-old", version_id="v1", is_latest=True, verified=True
        )
    ]


def test_activation_steps_never_expose_unverified_or_dual_versions() -> None:
    store = ActivationStore()
    _seed_old(store)
    assert store.query_visible_versions("doc-1") == ["v1"]

    activate_version(
        store,
        document_id="doc-1",
        old_version_id="v1",
        new_version_id="v2",
        new_point_ids=["p-new"],
    )
    assert store.activation_step["doc-1"] == 5
    assert store.query_visible_versions("doc-1") == ["v2"]
    assert len(store.query_visible_versions("doc-1")) == 1
    by_version = {p.version_id: p.is_latest for p in store.points["doc-1"]}
    assert by_version["v2"] is True
    assert by_version["v1"] is False


def test_interrupted_activation_resumes_from_recorded_step() -> None:
    store = ActivationStore()
    _seed_old(store)
    # Interrupted after step 2: new points is_latest=true; metadata still old.
    store.points["doc-1"].append(
        VectorPointState(
            point_id="p-new", version_id="v2", is_latest=True, verified=True
        )
    )
    store.activation_step["doc-1"] = 2
    assert store.query_visible_versions("doc-1") == ["v1"]

    step = reconcile_activation(
        store,
        document_id="doc-1",
        old_version_id="v1",
        new_version_id="v2",
        new_point_ids=["p-new"],
    )
    assert step == 5
    assert store.query_visible_versions("doc-1") == ["v2"]
    assert "activated:doc-1:v2" in store.audit


def test_guard_never_returns_two_versions() -> None:
    store = ActivationStore()
    store.set_current("doc-1", "v2")
    store.points["doc-1"] = [
        VectorPointState("a", "v1", True, True),
        VectorPointState("b", "v2", True, True),
    ]
    assert store.query_visible_versions("doc-1") == ["v2"]
