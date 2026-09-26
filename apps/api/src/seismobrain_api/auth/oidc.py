"""
File: oidc.py
Description: OIDC SSO with group-claim mapping (FR-AUTH-06)
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
from typing import Protocol

from seismobrain_core.principal_epoch import PrincipalSet, bump_principal_authz_epochs


class OidcTokenVerifier(Protocol):
    def verify_id_token(self, token: str) -> dict[str, object]:
        """Validate token and return claims."""


@dataclass
class MockOidcProvider:
    """Test double for OIDC provider."""

    tokens: dict[str, dict[str, object]] = field(default_factory=dict)

    def verify_id_token(self, token: str) -> dict[str, object]:
        if token not in self.tokens:
            raise ValueError("invalid token")
        return dict(self.tokens[token])


@dataclass
class OidcSettings:
    enabled: bool = True
    local_login_disabled: bool = False
    group_claim: str = "groups"


@dataclass
class OidcService:
    settings: OidcSettings
    verifier: OidcTokenVerifier
    # external group name -> internal group id
    group_map: dict[str, str] = field(default_factory=dict)
    principals: dict[str, PrincipalSet] = field(default_factory=dict)

    def authenticate(self, id_token: str) -> dict[str, object]:
        claims = self.verifier.verify_id_token(id_token)
        sub = str(claims.get("sub", ""))
        if not sub:
            raise ValueError("missing sub")
        raw_groups = claims.get(self.settings.group_claim, [])
        if not isinstance(raw_groups, list):
            raw_groups = []
        mapped = {
            self.group_map[name]
            for name in raw_groups
            if isinstance(name, str) and name in self.group_map
        }
        current = self.principals.get(
            sub, PrincipalSet(user_id=sub, group_ids=frozenset(), epoch=0)
        )
        previous = current.group_ids
        updated = PrincipalSet(user_id=sub, group_ids=frozenset(mapped), epoch=current.epoch)
        self.principals[sub] = updated
        if previous != updated.group_ids:
            self.principals = bump_principal_authz_epochs(
                self.principals, changed_user_id=sub
            )
        return {
            "user_id": sub,
            "groups": sorted(updated.group_ids),
            "epoch": self.principals[sub].epoch,
            "local_login_disabled": self.settings.local_login_disabled,
        }

    def local_login_allowed(self) -> bool:
        return not self.settings.local_login_disabled
