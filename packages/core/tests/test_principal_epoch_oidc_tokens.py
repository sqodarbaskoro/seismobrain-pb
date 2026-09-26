"""
File: test_principal_epoch_oidc_tokens.py
Description: Principal epoch on OIDC sync and token revocation (T4.6)
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

from seismobrain_api.auth.api_tokens import InMemoryApiTokenStore
from seismobrain_api.auth.oidc import MockOidcProvider, OidcService, OidcSettings
from seismobrain_core.principal_epoch import PrincipalSet, bump_principal_authz_epochs


def test_oidc_group_sync_bumps_epoch() -> None:
    service = OidcService(
        settings=OidcSettings(),
        verifier=MockOidcProvider(
            tokens={"t1": {"sub": "u1", "groups": ["Eng"]}}
        ),
        group_map={"Eng": "g1"},
        principals={
            "u1": PrincipalSet(user_id="u1", group_ids=frozenset(), epoch=3)
        },
    )
    result = service.authenticate("t1")
    assert result["epoch"] == 4
    assert service.principals["u1"].group_ids == frozenset({"g1"})


def test_token_revocation_bumps_epoch() -> None:
    store = InMemoryApiTokenStore()
    record, _raw = store.issue(
        owner_id="u1", name="x", scopes={"read"}, ttl_seconds=60
    )
    store.revoke(record.id)
    users = {"u1": PrincipalSet(user_id="u1", group_ids=frozenset(), epoch=1)}
    updated = bump_principal_authz_epochs(users, changed_user_id="u1")
    assert updated["u1"].epoch == 2
