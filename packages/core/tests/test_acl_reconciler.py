"""
File: test_acl_reconciler.py
Description: acl_sync_state reconciler with vector-store outage (FR-ACL-11)
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

import pytest

from seismobrain_core.acl_reconciler import (
    AclReconciler,
    AclSyncState,
    VectorSyncError,
)


class _FlakyVectorTarget:
    def __init__(self, *, fail_times: int) -> None:
        self.fail_times = fail_times
        self.calls = 0
        self.synced_epoch = 0

    def sync_acl(
        self, resource_type: str, resource_id: str, acl_epoch: int, principals: list[str]
    ) -> None:
        _ = resource_type, resource_id, principals
        self.calls += 1
        if self.calls <= self.fail_times:
            raise VectorSyncError("vector store unavailable")
        self.synced_epoch = acl_epoch


def test_reconciler_retries_until_vector_matches() -> None:
    state = AclSyncState(
        resource_type="collection",
        resource_id="c1",
        acl_epoch=3,
        synced_epoch=1,
        status="pending",
    )
    target = _FlakyVectorTarget(fail_times=2)
    reconciler = AclReconciler(target)
    result = reconciler.reconcile(state, principals=["u:u1"], max_attempts=5)
    assert result.status == "synced"
    assert result.synced_epoch == 3
    assert target.synced_epoch == 3
    assert target.calls == 3


def test_reconciler_records_outage_and_keeps_pending() -> None:
    state = AclSyncState(
        resource_type="document",
        resource_id="d1",
        acl_epoch=2,
        synced_epoch=0,
        status="pending",
    )
    target = _FlakyVectorTarget(fail_times=10)
    reconciler = AclReconciler(target)
    with pytest.raises(VectorSyncError):
        reconciler.reconcile(state, principals=["u:u1"], max_attempts=3)
    assert state.status == "error"
    assert state.synced_epoch == 0
    assert state.last_error is not None
    assert "unavailable" in state.last_error


def test_already_synced_is_noop() -> None:
    state = AclSyncState(
        resource_type="collection",
        resource_id="c1",
        acl_epoch=1,
        synced_epoch=1,
        status="synced",
    )
    target = _FlakyVectorTarget(fail_times=0)
    reconciler = AclReconciler(target)
    result = reconciler.reconcile(state, principals=["u:u1"], max_attempts=3)
    assert result.status == "synced"
    assert target.calls == 0
