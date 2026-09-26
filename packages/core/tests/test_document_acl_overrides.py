"""
File: test_document_acl_overrides.py
Description: Document-level restrictive ACL overrides (T4.2)
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
from seismobrain_core.permissions import Permission


def test_document_restrictive_override_lowers_inherited_write() -> None:
    principal = Principal("user", "u1")
    entries = [
        AclEntry(ResourceRef("collection", "c1"), principal, Permission.WRITE),
        AclEntry(ResourceRef("document", "d1"), principal, Permission.READ),
    ]
    granted = effective_permission(
        entries,
        resource=ResourceRef("document", "d1"),
        principal=principal,
        collection_id="c1",
    )
    assert granted == Permission.READ


def test_document_override_cannot_expand_beyond_collection() -> None:
    principal = Principal("user", "u1")
    entries = [
        AclEntry(ResourceRef("collection", "c1"), principal, Permission.READ),
        AclEntry(ResourceRef("document", "d1"), principal, Permission.MANAGE),
    ]
    granted = effective_permission(
        entries,
        resource=ResourceRef("document", "d1"),
        principal=principal,
        collection_id="c1",
    )
    assert granted == Permission.READ
