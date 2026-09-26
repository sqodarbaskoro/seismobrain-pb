"""
File: test_acl_asymmetric.py
Description: Asymmetric ACL grant/revoke semantics and acl_epoch (FR-ACL-06)
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

from seismobrain_core.acl_asymmetric import AclChangeLog, AclResourceState
from seismobrain_core.permissions import Permission


def test_grant_waits_for_vector_sync() -> None:
    state = AclResourceState(resource_type="collection", resource_id="c1")
    audit = AclChangeLog()
    state.grant("user", "u1", Permission.READ, audit=audit)
    assert state.acl_epoch == 1
    assert state.synced_epoch == 0
    assert state.sync_lag() == 1
    # Guard before sync: grant not yet visible.
    assert state.guard_allows("user", "u1", Permission.READ) is False
    state.confirm_vector_sync(epoch=1)
    assert state.synced_epoch == 1
    assert state.sync_lag() == 0
    assert state.guard_allows("user", "u1", Permission.READ) is True
    assert audit.events[-1].action == "grant"


def test_revoke_is_immediate_even_if_sync_pending() -> None:
    state = AclResourceState(resource_type="collection", resource_id="c1")
    audit = AclChangeLog()
    state.grant("user", "u1", Permission.READ, audit=audit)
    state.confirm_vector_sync(epoch=1)
    assert state.guard_allows("user", "u1", Permission.READ) is True

    state.revoke("user", "u1", audit=audit)
    assert state.acl_epoch == 2
    # Revocation effective immediately via guard, even while synced_epoch lags.
    assert state.synced_epoch == 1
    assert state.sync_lag() == 1
    assert state.guard_allows("user", "u1", Permission.READ) is False
    assert audit.events[-1].action == "revoke"


def test_acl_change_increments_epoch_and_audits() -> None:
    state = AclResourceState(resource_type="document", resource_id="d1")
    audit = AclChangeLog()
    assert state.acl_epoch == 0
    state.grant("group", "g1", Permission.WRITE, audit=audit)
    state.revoke("group", "g1", audit=audit)
    assert state.acl_epoch == 2
    assert [e.action for e in audit.events] == ["grant", "revoke"]
    assert all(e.acl_epoch > 0 for e in audit.events)
