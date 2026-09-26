"""
File: test_authz_version_guard.py
Description: Post-fusion authz + version guard tests (FR-ACL-09)
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

import time

from seismobrain_core.authz_version_guard import (
    FusionCandidate,
    guard_after_fusion,
)


class _Store:
    def __init__(self) -> None:
        self.read: dict[tuple[str, str], bool] = {}
        self.current: dict[str, str] = {}
        self.resource_epochs: dict[str, int] = {}
        self.principal_epochs: dict[str, int] = {}

    def check_read(self, user_id: str, document_id: str) -> bool:
        return self.read.get((user_id, document_id), False)

    def current_version_id(self, document_id: str) -> str:
        return self.current[document_id]

    def resource_acl_epoch(self, document_id: str) -> int:
        return self.resource_epochs.get(document_id, 0)

    def principal_authz_epoch(self, user_id: str) -> int:
        return self.principal_epochs.get(user_id, 0)


def test_revoked_and_stale_versions_dropped() -> None:
    store = _Store()
    store.read[("u1", "d1")] = True
    store.read[("u1", "d2")] = False  # revoked
    store.current["d1"] = "v2"
    store.current["d2"] = "v9"
    store.resource_epochs["d1"] = 1
    store.resource_epochs["d2"] = 1
    store.principal_epochs["u1"] = 1
    candidates = [
        FusionCandidate(document_id="d1", version_id="v2", score=1.0),
        FusionCandidate(document_id="d1", version_id="v1", score=0.9),  # stale
        FusionCandidate(document_id="d2", version_id="v9", score=0.8),
    ]
    kept, drops = guard_after_fusion(store, user_id="u1", candidates=candidates)
    assert [c.document_id for c in kept] == ["d1"]
    assert kept[0].version_id == "v2"
    assert drops["revoked"] == 1
    assert drops["stale_version"] == 1


def test_guard_p95_under_30ms_for_150_candidates() -> None:
    store = _Store()
    store.principal_epochs["u1"] = 1
    candidates: list[FusionCandidate] = []
    for i in range(150):
        doc = f"d{i}"
        store.read[("u1", doc)] = True
        store.current[doc] = "v1"
        store.resource_epochs[doc] = 1
        candidates.append(FusionCandidate(document_id=doc, version_id="v1", score=1.0))
    started = time.perf_counter()
    kept, _ = guard_after_fusion(store, user_id="u1", candidates=candidates)
    elapsed_ms = (time.perf_counter() - started) * 1000
    assert len(kept) == 150
    assert elapsed_ms <= 30.0
