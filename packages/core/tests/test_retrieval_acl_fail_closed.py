"""
File: test_retrieval_acl_fail_closed.py
Description: Retrieval fails closed without server-built ACL filter (FR-ACL-05, SEC-23)
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

from seismobrain_core.retrieval import (
    AclFilterMissingError,
    RetrievalRequest,
    build_acl_filter,
    run_retrieval,
)


def test_missing_acl_filter_fails_closed() -> None:
    request = RetrievalRequest(
        tenant_id="t1",
        query_vector=[0.1, 0.2],
        acl_filter=None,
    )
    with pytest.raises(AclFilterMissingError):
        run_retrieval(request, search=lambda **_: [])


def test_server_built_filter_required_on_request() -> None:
    acl = build_acl_filter(
        tenant_id="t1",
        principal_ids=["user:alice"],
        require_latest=True,
    )
    assert acl.tenant_id == "t1"
    assert "user:alice" in acl.principal_ids
    assert acl.require_latest is True
    hits = run_retrieval(
        RetrievalRequest(tenant_id="t1", query_vector=[0.1], acl_filter=acl),
        search=lambda **kwargs: [{"id": "p1", "filter": kwargs["acl_filter"]}],
    )
    assert hits[0]["filter"] is acl
