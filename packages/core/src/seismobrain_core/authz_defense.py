"""
File: authz_defense.py
Description: Defense-in-depth vector filter + metadata guard (SEC-23)
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

from seismobrain_core.authorization_guard import CachingAuthorizationGuard, MetadataAuthzStore
from seismobrain_core.retrieval import AclFilter, AclFilterMissingError


@dataclass(frozen=True)
class CandidateHit:
    document_id: str
    version_id: str
    acl: list[str]


def authorize_candidates(
    store: MetadataAuthzStore,
    *,
    user_id: str,
    tenant_id: str,
    acl_filter: AclFilter | None,
    hits: list[CandidateHit],
) -> list[CandidateHit]:
    """Require vector ACL filter and authoritative metadata guard for every hit."""
    if acl_filter is None:
        raise AclFilterMissingError("retrieval requires a server-built ACL filter")
    if acl_filter.tenant_id != tenant_id:
        raise AclFilterMissingError("ACL filter tenant mismatch")
    guard = CachingAuthorizationGuard(store)
    principals = set(acl_filter.principal_ids)
    kept: list[CandidateHit] = []
    for hit in hits:
        if not principals.intersection(hit.acl):
            continue
        if not guard.check_read(user_id, hit.document_id):
            continue
        kept.append(hit)
    return kept
