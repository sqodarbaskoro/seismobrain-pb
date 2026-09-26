"""
File: acl.py
Description: ACL entries and collection→document inheritance (FR-ACL-03)
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

from seismobrain_core.permissions import Permission


@dataclass(frozen=True, slots=True)
class Principal:
    principal_type: str
    principal_id: str


@dataclass(frozen=True, slots=True)
class ResourceRef:
    resource_type: str
    resource_id: str


@dataclass(frozen=True, slots=True)
class AclEntry:
    resource: ResourceRef
    principal: Principal
    permission: Permission


def effective_permission(
    entries: list[AclEntry],
    *,
    resource: ResourceRef,
    principal: Principal,
    collection_id: str | None = None,
) -> Permission | None:
    """
    Resolve the caller's permission on a resource.

    Documents inherit collection ACLs (FR-ACL-03). Document-level entries are
    restrictive overrides: they may only lower (or equal) the inherited grant.
    """
    inherited: Permission | None = None
    document_override: Permission | None = None
    for entry in entries:
        if entry.principal != principal:
            continue
        if entry.resource == resource:
            if resource.resource_type == "document":
                if document_override is None or entry.permission < document_override:
                    document_override = entry.permission
            else:
                if inherited is None or entry.permission > inherited:
                    inherited = entry.permission
            continue
        if (
            resource.resource_type == "document"
            and collection_id is not None
            and entry.resource.resource_type == "collection"
            and entry.resource.resource_id == collection_id
        ):
            if inherited is None or entry.permission > inherited:
                inherited = entry.permission
    if document_override is not None:
        if inherited is None:
            return document_override
        return min(inherited, document_override)
    return inherited
