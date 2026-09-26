"""
File: test_authz_defense_in_depth.py
Description: Vector ACL filter plus metadata guard defense in depth (SEC-23)
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

from seismobrain_core.authz_defense import CandidateHit, authorize_candidates
from seismobrain_core.retrieval import build_acl_filter


class _Meta:
    def __init__(self) -> None:
        self.allowed = {("u1", "d1")}
        self.epochs = {"d1": 1, "d2": 1}
        self.principal = {"u1": 1}

    def check_read(self, user_id: str, document_id: str) -> bool:
        return (user_id, document_id) in self.allowed

    def resource_acl_epoch(self, document_id: str) -> int:
        return self.epochs.get(document_id, 0)

    def principal_authz_epoch(self, user_id: str) -> int:
        return self.principal.get(user_id, 0)


def test_vector_filter_and_metadata_guard_both_required() -> None:
    meta = _Meta()
    acl = build_acl_filter(tenant_id="t1", principal_ids=["user:u1"])
    # Vector arm still returns a revoked doc (sync lag); guard drops it immediately.
    hits = [
        CandidateHit(document_id="d1", version_id="v1", acl=["user:u1"]),
        CandidateHit(document_id="d2", version_id="v1", acl=["user:u1"]),
    ]
    meta.allowed.discard(("u1", "d2"))
    kept = authorize_candidates(
        meta,
        user_id="u1",
        tenant_id="t1",
        acl_filter=acl,
        hits=hits,
    )
    assert [h.document_id for h in kept] == ["d1"]


def test_missing_vector_filter_fails_closed() -> None:
    meta = _Meta()
    hits = [CandidateHit(document_id="d1", version_id="v1", acl=["user:u1"])]
    try:
        authorize_candidates(
            meta,
            user_id="u1",
            tenant_id="t1",
            acl_filter=None,
            hits=hits,
        )
        raise AssertionError("expected failure")
    except ValueError as exc:
        assert "ACL filter" in str(exc)
