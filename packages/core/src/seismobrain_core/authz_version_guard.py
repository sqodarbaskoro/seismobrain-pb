"""
File: authz_version_guard.py
Description: Post-fusion authorization and version guard (FR-ACL-09)
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

from seismobrain_core.authorization_guard import CachingAuthorizationGuard


class VersionAwareAuthzStore(Protocol):
    def check_read(self, user_id: str, document_id: str) -> bool: ...

    def current_version_id(self, document_id: str) -> str: ...

    def resource_acl_epoch(self, document_id: str) -> int: ...

    def principal_authz_epoch(self, user_id: str) -> int: ...


@dataclass(frozen=True)
class FusionCandidate:
    document_id: str
    version_id: str
    score: float


def guard_after_fusion(
    store: VersionAwareAuthzStore,
    *,
    user_id: str,
    candidates: list[FusionCandidate],
) -> tuple[list[FusionCandidate], dict[str, int]]:
    """
    Re-check read permission and current_version_id after fusion, before rerank.
    """
    guard = CachingAuthorizationGuard(store)
    kept: list[FusionCandidate] = []
    drops = {"revoked": 0, "stale_version": 0}
    for candidate in candidates:
        if not guard.check_read(user_id, candidate.document_id):
            drops["revoked"] += 1
            continue
        if candidate.version_id != store.current_version_id(candidate.document_id):
            drops["stale_version"] += 1
            continue
        kept.append(candidate)
    return kept, drops
