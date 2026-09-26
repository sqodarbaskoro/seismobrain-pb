"""
File: test_tenant_idf_isolation.py
Description: Tenant IDF isolation security check (T4.28)
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


def test_tenant_idf_filters_do_not_overlap() -> None:
    a = resolve_idf_corpus_filter(
        scope=IdfScope.TENANT, tenant_id="tenant-a", workspace_id="w1"
    )
    b = resolve_idf_corpus_filter(
        scope=IdfScope.TENANT, tenant_id="tenant-b", workspace_id="w2"
    )
    assert a != b
    assert a["tenant_id"] == "tenant-a"
    assert b["tenant_id"] == "tenant-b"
