"""
File: test_principal_epoch_group_removal.py
Description: Group membership removal blocks docs via principal epoch (FR-ACL-12)
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
from seismobrain_core.principal_epoch import PrincipalSet, bump_principal_authz_epochs


class _Store:
    def __init__(self) -> None:
        self.group_docs = {"g1": {"d1"}}
        self.users = {
            "u1": PrincipalSet(user_id="u1", group_ids=frozenset({"g1"}), epoch=1)
        }

    def check_read(self, user_id: str, document_id: str) -> bool:
        principal = self.users[user_id]
        for group_id in principal.group_ids:
            if document_id in self.group_docs.get(group_id, set()):
                return True
        return False

    def resource_acl_epoch(self, document_id: str) -> int:
        return 1

    def principal_authz_epoch(self, user_id: str) -> int:
        return self.users[user_id].epoch


def test_removing_user_from_group_blocks_next_request() -> None:
    store = _Store()
    guard = CachingAuthorizationGuard(store)
    assert guard.check_read("u1", "d1") is True
    # Remove group membership and bump principal epoch.
    store.users = {
        "u1": PrincipalSet(user_id="u1", group_ids=frozenset(), epoch=1),
    }
    store.users = bump_principal_authz_epochs(store.users, changed_user_id="u1")
    assert store.users["u1"].epoch == 2
    assert guard.check_read("u1", "d1") is False
