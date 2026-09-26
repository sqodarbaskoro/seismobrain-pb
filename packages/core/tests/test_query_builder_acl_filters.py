"""
File: test_query_builder_acl_filters.py
Description: FR-RET-01 / FR-ACL-05 — identical hard filters on every prefetch arm + root
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

from seismobrain_core.query_builder import HardFilter, PrefetchArm, build_query
from seismobrain_core.retrieval import AclFilterMissingError


def test_three_arms_when_identifiers_present_share_identical_hard_filter() -> None:
    hard = HardFilter(
        tenant_id="t1",
        workspace_id="w1",
        collection_ids=("c1",),
        acl_principals=("u:alice",),
        require_latest=True,
        metadata={"doc_type": "pdf"},
    )
    query = build_query(
        text="Clear E-404 on well-alpha-12",
        hard_filter=hard,
        has_identifiers=True,
    )
    assert query.root_filter == hard
    assert {arm.name for arm in query.prefetch} == {"dense", "bm25_text", "ident"}
    for arm in query.prefetch:
        assert arm.hard_filter == hard
        assert arm.hard_filter is query.root_filter or arm.hard_filter == query.root_filter


def test_ident_arm_omitted_without_identifiers() -> None:
    hard = HardFilter(
        tenant_id="t1",
        workspace_id="w1",
        collection_ids=("c1",),
        acl_principals=("u:alice",),
    )
    query = build_query(text="pump seal procedure", hard_filter=hard, has_identifiers=False)
    assert [arm.name for arm in query.prefetch] == ["dense", "bm25_text"]


def test_missing_hard_filter_fails_closed() -> None:
    with pytest.raises(AclFilterMissingError):
        build_query(text="x", hard_filter=None, has_identifiers=False)


def test_prefetch_arm_type() -> None:
    assert PrefetchArm(name="dense", hard_filter=HardFilter(
        tenant_id="t", workspace_id="w", collection_ids=(), acl_principals=("u:a",)
    )).name == "dense"
