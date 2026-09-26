"""
File: test_revocation_race.py
Description: Revocation race — guard drops after principal epoch bump (T4.28)
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


class _Store:
    def __init__(self) -> None:
        self.allowed = {("u1", "d1")}
        self.principal = {"u1": 1}
        self.resource = {"d1": 1}

    def check_read(self, user_id: str, document_id: str) -> bool:
        return (user_id, document_id) in self.allowed

    def resource_acl_epoch(self, document_id: str) -> int:
        return self.resource[document_id]

    def principal_authz_epoch(self, user_id: str) -> int:
        return self.principal[user_id]


def test_revocation_invalidates_guard_cache_immediately() -> None:
    store = _Store()
    guard = CachingAuthorizationGuard(store)
    assert guard.check_read("u1", "d1") is True
    store.allowed.discard(("u1", "d1"))
    store.principal["u1"] += 1
    assert guard.check_read("u1", "d1") is False
