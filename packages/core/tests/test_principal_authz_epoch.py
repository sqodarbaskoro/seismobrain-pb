"""
File: test_principal_authz_epoch.py
Description: Principal authorization epoch increments (FR-ACL-12)
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

from seismobrain_core.principal_epoch import PrincipalSet, bump_principal_authz_epochs


def test_group_membership_change_bumps_affected_users_only() -> None:
    users = {
        "u1": PrincipalSet(user_id="u1", group_ids=frozenset({"g1"}), epoch=1),
        "u2": PrincipalSet(user_id="u2", group_ids=frozenset({"g1", "g2"}), epoch=4),
        "u3": PrincipalSet(user_id="u3", group_ids=frozenset({"g2"}), epoch=2),
    }
    updated = bump_principal_authz_epochs(users, changed_group_id="g1")
    assert updated["u1"].epoch == 2
    assert updated["u2"].epoch == 5
    assert updated["u3"].epoch == 2  # unaffected


def test_direct_principal_change_bumps_single_user() -> None:
    users = {
        "u1": PrincipalSet(user_id="u1", group_ids=frozenset(), epoch=0),
        "u2": PrincipalSet(user_id="u2", group_ids=frozenset({"g9"}), epoch=9),
    }
    updated = bump_principal_authz_epochs(users, changed_user_id="u1")
    assert updated["u1"].epoch == 1
    assert updated["u2"].epoch == 9


def test_does_not_mutate_document_acl_epochs() -> None:
    users = {"u1": PrincipalSet(user_id="u1", group_ids=frozenset({"g1"}), epoch=3)}
    doc_acl_epoch = 10
    bump_principal_authz_epochs(users, changed_group_id="g1")
    assert doc_acl_epoch == 10
