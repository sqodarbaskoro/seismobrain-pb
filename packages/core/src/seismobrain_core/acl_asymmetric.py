"""
File: acl_asymmetric.py
Description: Asymmetric ACL grant/revoke semantics with acl_epoch (FR-ACL-06)
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

from seismobrain_core.permissions import Permission


@dataclass(frozen=True, slots=True)
class AclAuditEvent:
    action: str
    resource_type: str
    resource_id: str
    principal_type: str
    principal_id: str
    acl_epoch: int


@dataclass
class AclChangeLog:
    events: list[AclAuditEvent] = field(default_factory=list)

    def record(self, event: AclAuditEvent) -> None:
        self.events.append(event)


@dataclass
class _Grant:
    permission: Permission
    grant_epoch: int
    revoked: bool = False
    revoke_epoch: int | None = None


@dataclass
class AclResourceState:
    """Tracks desired ACL epoch vs vector-synced epoch for one resource."""

    resource_type: str
    resource_id: str
    acl_epoch: int = 0
    synced_epoch: int = 0
    _grants: dict[tuple[str, str], _Grant] = field(default_factory=dict)

    def sync_lag(self) -> int:
        return max(0, self.acl_epoch - self.synced_epoch)

    def grant(
        self,
        principal_type: str,
        principal_id: str,
        permission: Permission,
        *,
        audit: AclChangeLog,
    ) -> None:
        self.acl_epoch += 1
        key = (principal_type, principal_id)
        self._grants[key] = _Grant(permission=permission, grant_epoch=self.acl_epoch)
        audit.record(
            AclAuditEvent(
                action="grant",
                resource_type=self.resource_type,
                resource_id=self.resource_id,
                principal_type=principal_type,
                principal_id=principal_id,
                acl_epoch=self.acl_epoch,
            )
        )

    def revoke(
        self,
        principal_type: str,
        principal_id: str,
        *,
        audit: AclChangeLog,
    ) -> None:
        self.acl_epoch += 1
        key = (principal_type, principal_id)
        existing = self._grants.get(key)
        if existing is not None:
            existing.revoked = True
            existing.revoke_epoch = self.acl_epoch
        audit.record(
            AclAuditEvent(
                action="revoke",
                resource_type=self.resource_type,
                resource_id=self.resource_id,
                principal_type=principal_type,
                principal_id=principal_id,
                acl_epoch=self.acl_epoch,
            )
        )

    def confirm_vector_sync(self, *, epoch: int) -> None:
        if epoch > self.synced_epoch:
            self.synced_epoch = epoch

    def guard_allows(
        self,
        principal_type: str,
        principal_id: str,
        needed: Permission,
    ) -> bool:
        """Authoritative guard view: revocations immediate; grants after sync."""
        grant = self._grants.get((principal_type, principal_id))
        if grant is None:
            return False
        if grant.revoked:
            return False
        if grant.grant_epoch > self.synced_epoch:
            return False
        return grant.permission >= needed
