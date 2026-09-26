"""
File: test_historical_search.py
Description: Historical search explicit audited mode (T4.10)
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

from seismobrain_core.historical_search import (
    HistoricalAuditLog,
    HistoricalHit,
    HistoricalScope,
    build_historical_hard_filter,
    guard_historical,
    label_historical_hit,
)
from seismobrain_core.query_builder import HardFilter


class _Store:
    def __init__(self) -> None:
        self.allowed = {("u1", "d1"), ("u1", "d2")}
        self._p = {"u1": 1}
        self._r = {"d1": 1, "d2": 1, "d3": 1}

    def check_read(self, user_id: str, document_id: str) -> bool:
        return (user_id, document_id) in self.allowed

    def resource_acl_epoch(self, document_id: str) -> int:
        return self._r[document_id]

    def principal_authz_epoch(self, user_id: str) -> int:
        return self._p[user_id]


def test_historical_mode_scope_guard_and_labels() -> None:
    scope = HistoricalScope(
        document_ids=frozenset({"d1", "d2"}),
        from_date="2024-01-01",
        to_date="2024-12-31",
    )
    audit = HistoricalAuditLog()
    audit.record(user_id="u1", scope=scope)
    assert audit.entries

    base = HardFilter(
        tenant_id="t1",
        workspace_id="w1",
        collection_ids=("c1",),
        acl_principals=("user:u1",),
        require_latest=True,
    )
    filt = build_historical_hard_filter(base, scope)
    assert filt.require_latest is False
    assert filt.metadata["version_from"] == "2024-01-01"

    candidates = [
        HistoricalHit("d1", "v1", "2024-06-01", 1.0),
        HistoricalHit("d1", "v0", "2023-01-01", 0.9),  # out of range
        HistoricalHit("d3", "v1", "2024-06-01", 0.8),  # out of doc scope
        HistoricalHit("d2", "v2", "2024-07-01", 0.7),  # revoked below
    ]
    store = _Store()
    store.allowed.add(("u1", "d3"))  # readable but outside historical doc scope
    store.allowed.discard(("u1", "d2"))
    kept, drops = guard_historical(
        store, user_id="u1", scope=scope, candidates=candidates
    )
    assert [h.document_id for h in kept] == ["d1"]
    assert drops["out_of_scope"] >= 2
    assert drops["revoked"] == 1
    labelled = label_historical_hit(kept[0])
    assert "v=v1" in labelled.citation_label
    assert "2024-06-01" in labelled.citation_label
