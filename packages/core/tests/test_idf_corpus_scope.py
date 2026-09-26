"""
File: test_idf_corpus_scope.py
Description: FR-RET-12 / SEC-24 — tenant-scoped IDF corpus with empty fallback
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

from seismobrain_core.idf_scope import IdfScope, resolve_idf_corpus_filter


def test_default_idf_scope_is_tenant() -> None:
    filt = resolve_idf_corpus_filter(
        tenant_id="tenant-a",
        workspace_id="ws-1",
        scope=IdfScope.TENANT,
        workspace_point_count=0,
    )
    assert filt == {"tenant_id": "tenant-a"}
    assert "workspace_id" not in filt


def test_tenant_b_docs_do_not_enter_tenant_a_idf_filter() -> None:
    filt_a = resolve_idf_corpus_filter(
        tenant_id="tenant-a",
        workspace_id="ws-1",
        scope=IdfScope.TENANT,
        workspace_point_count=10,
    )
    filt_b = resolve_idf_corpus_filter(
        tenant_id="tenant-b",
        workspace_id="ws-9",
        scope=IdfScope.TENANT,
        workspace_point_count=10,
    )
    assert filt_a["tenant_id"] == "tenant-a"
    assert filt_b["tenant_id"] == "tenant-b"
    assert filt_a != filt_b


def test_empty_workspace_corpus_falls_back_to_tenant() -> None:
    filt = resolve_idf_corpus_filter(
        tenant_id="tenant-a",
        workspace_id="ws-empty",
        scope=IdfScope.WORKSPACE,
        workspace_point_count=0,
    )
    assert filt == {"tenant_id": "tenant-a"}


def test_workspace_scope_when_corpus_nonempty() -> None:
    filt = resolve_idf_corpus_filter(
        tenant_id="tenant-a",
        workspace_id="ws-1",
        scope=IdfScope.WORKSPACE,
        workspace_point_count=3,
    )
    assert filt == {"tenant_id": "tenant-a", "workspace_id": "ws-1"}
