"""
File: test_acl_inheritance.py
Description: Collection ACL inheritance to documents (FR-ACL-03)
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

from seismobrain_core.acl import AclEntry, Principal, ResourceRef, effective_permission
from seismobrain_core.permissions import Action, Permission, allows


def test_document_inherits_collection_acl() -> None:
    collection = ResourceRef(resource_type="collection", resource_id="c1")
    document = ResourceRef(resource_type="document", resource_id="d1")
    principal = Principal(principal_type="user", principal_id="u1")
    entries = [
        AclEntry(
            resource=collection,
            principal=principal,
            permission=Permission.READ,
        )
    ]
    granted = effective_permission(
        entries,
        resource=document,
        principal=principal,
        collection_id="c1",
    )
    assert granted == Permission.READ
    assert allows(granted, Action.QUERY) is True


def test_unrelated_collection_acl_does_not_apply() -> None:
    entries = [
        AclEntry(
            resource=ResourceRef("collection", "other"),
            principal=Principal("user", "u1"),
            permission=Permission.MANAGE,
        )
    ]
    granted = effective_permission(
        entries,
        resource=ResourceRef("document", "d1"),
        principal=Principal("user", "u1"),
        collection_id="c1",
    )
    assert granted is None


def test_highest_inherited_permission_wins() -> None:
    principal = Principal("user", "u1")
    entries = [
        AclEntry(ResourceRef("collection", "c1"), principal, Permission.READ),
        AclEntry(ResourceRef("collection", "c1"), principal, Permission.WRITE),
    ]
    granted = effective_permission(
        entries,
        resource=ResourceRef("document", "d1"),
        principal=principal,
        collection_id="c1",
    )
    assert granted == Permission.WRITE
