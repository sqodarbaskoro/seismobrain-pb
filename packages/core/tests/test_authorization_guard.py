"""
File: test_authorization_guard.py
Description: AuthorizationGuard with epoch-keyed cache (FR-ACL-09)
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

from seismobrain_core.authorization_guard import CachingAuthorizationGuard


class _MetaStore:
    def __init__(self) -> None:
        self.calls = 0
        self._allowed: dict[tuple[str, str], bool] = {}
        self._resource_epochs: dict[str, int] = {}
        self._principal_epochs: dict[str, int] = {}

    def set_allow(self, user_id: str, document_id: str, allowed: bool) -> None:
        self._allowed[(user_id, document_id)] = allowed

    def set_resource_epoch(self, document_id: str, epoch: int) -> None:
        self._resource_epochs[document_id] = epoch

    def set_principal_epoch(self, user_id: str, epoch: int) -> None:
        self._principal_epochs[user_id] = epoch

    def check_read(self, user_id: str, document_id: str) -> bool:
        self.calls += 1
        return self._allowed.get((user_id, document_id), False)

    def resource_acl_epoch(self, document_id: str) -> int:
        return self._resource_epochs.get(document_id, 0)

    def principal_authz_epoch(self, user_id: str) -> int:
        return self._principal_epochs.get(user_id, 0)


def test_guard_rechecks_and_caches_by_epochs() -> None:
    store = _MetaStore()
    store.set_allow("u1", "d1", True)
    store.set_resource_epoch("d1", 1)
    store.set_principal_epoch("u1", 1)
    guard = CachingAuthorizationGuard(store)

    assert guard.check_read("u1", "d1") is True
    assert guard.check_read("u1", "d1") is True
    assert store.calls == 1  # cache hit

    store.set_principal_epoch("u1", 2)
    store.set_allow("u1", "d1", False)
    assert guard.check_read("u1", "d1") is False
    assert store.calls == 2  # principal epoch change busts cache


def test_resource_acl_epoch_change_busts_cache() -> None:
    store = _MetaStore()
    store.set_allow("u1", "d1", True)
    store.set_resource_epoch("d1", 5)
    store.set_principal_epoch("u1", 1)
    guard = CachingAuthorizationGuard(store)
    assert guard.check_read("u1", "d1") is True
    store.set_resource_epoch("d1", 6)
    store.set_allow("u1", "d1", False)
    assert guard.check_read("u1", "d1") is False
    assert store.calls == 2


def test_guard_filters_candidates() -> None:
    store = _MetaStore()
    store.set_allow("u1", "d1", True)
    store.set_allow("u1", "d2", False)
    store.set_resource_epoch("d1", 1)
    store.set_resource_epoch("d2", 1)
    store.set_principal_epoch("u1", 1)
    guard = CachingAuthorizationGuard(store)
    kept = guard.filter_readable("u1", ["d1", "d2", "d1"])
    assert kept == ["d1", "d1"]
