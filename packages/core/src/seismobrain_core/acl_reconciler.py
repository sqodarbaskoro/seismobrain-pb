"""
File: acl_reconciler.py
Description: acl_sync_state tracking and vector ACL reconciler (FR-ACL-11)
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

from dataclasses import dataclass
from typing import Protocol


class VectorSyncError(RuntimeError):
    """Raised when the vector store cannot accept an ACL payload sync."""


class VectorSyncTarget(Protocol):
    def sync_acl(
        self,
        resource_type: str,
        resource_id: str,
        acl_epoch: int,
        principals: list[str],
    ) -> None:
        """Push desired ACL epoch/principals to the vector payload index."""


@dataclass
class AclSyncState:
    resource_type: str
    resource_id: str
    acl_epoch: int
    synced_epoch: int
    status: str
    last_error: str | None = None


class AclReconciler:
    """Retries vector ACL sync until synced_epoch matches acl_epoch."""

    def __init__(self, target: VectorSyncTarget) -> None:
        self._target = target

    def reconcile(
        self,
        state: AclSyncState,
        *,
        principals: list[str],
        max_attempts: int = 5,
    ) -> AclSyncState:
        if state.synced_epoch >= state.acl_epoch:
            state.status = "synced"
            state.last_error = None
            return state

        last_error: str | None = None
        for _ in range(max_attempts):
            try:
                self._target.sync_acl(
                    state.resource_type,
                    state.resource_id,
                    state.acl_epoch,
                    principals,
                )
                state.synced_epoch = state.acl_epoch
                state.status = "synced"
                state.last_error = None
                return state
            except VectorSyncError as exc:
                last_error = str(exc)
                state.status = "error"
                state.last_error = last_error

        raise VectorSyncError(last_error or "vector sync failed")
