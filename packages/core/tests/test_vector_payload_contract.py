"""
File: test_vector_payload_contract.py
Description: Vector point ACL payload contract tests (FR-ACL-04)
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

import pytest

from seismobrain_core.vector_payload import (
    REQUIRED_ACL_PAYLOAD_FIELDS,
    VectorAclPayload,
    validate_acl_payload,
)


def test_required_fields_present() -> None:
    assert REQUIRED_ACL_PAYLOAD_FIELDS == (
        "tenant_id",
        "workspace_id",
        "collection_id",
        "document_id",
        "version_id",
        "acl",
        "is_latest",
    )


def test_valid_payload_accepted() -> None:
    payload = VectorAclPayload(
        tenant_id="t1",
        workspace_id="w1",
        collection_id="c1",
        document_id="d1",
        version_id="v1",
        acl=["user:alice", "group:eng"],
        is_latest=True,
    )
    assert validate_acl_payload(payload.to_dict()) == payload


def test_missing_or_invalid_fields_rejected() -> None:
    base = {
        "tenant_id": "t1",
        "workspace_id": "w1",
        "collection_id": "c1",
        "document_id": "d1",
        "version_id": "v1",
        "acl": ["user:alice"],
        "is_latest": True,
    }
    for field in REQUIRED_ACL_PAYLOAD_FIELDS:
        bad = dict(base)
        del bad[field]
        with pytest.raises(ValueError, match=field):
            validate_acl_payload(bad)
    with pytest.raises(ValueError, match="acl"):
        validate_acl_payload({**base, "acl": "user:alice"})
    with pytest.raises(ValueError, match="is_latest"):
        validate_acl_payload({**base, "is_latest": "yes"})
