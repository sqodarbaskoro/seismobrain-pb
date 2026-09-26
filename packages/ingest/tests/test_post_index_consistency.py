"""
File: test_post_index_consistency.py
Description: FR-ING-10 — post-index metadata vs vector consistency
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

from seismobrain_ingest.post_index_consistency import (
    ConsistencyStores,
    verify_post_index,
)


def test_matching_counts_and_payloads_pass() -> None:
    stores = ConsistencyStores(
        metadata_chunk_ids={"v1": ["c1", "c2"]},
        vector_chunk_ids={"v1": ["c2", "c1"]},
        metadata_payloads={
            "c1": {"text_hash": "a", "version_id": "v1"},
            "c2": {"text_hash": "b", "version_id": "v1"},
        },
        vector_payloads={
            "c1": {"text_hash": "a", "version_id": "v1"},
            "c2": {"text_hash": "b", "version_id": "v1"},
        },
    )
    report = verify_post_index(stores, version_id="v1")
    assert report.ok is True
    assert report.alerts == ()


def test_mismatch_raises_alert() -> None:
    stores = ConsistencyStores(
        metadata_chunk_ids={"v1": ["c1", "c2"]},
        vector_chunk_ids={"v1": ["c1"]},
        metadata_payloads={
            "c1": {"text_hash": "a"},
            "c2": {"text_hash": "b"},
        },
        vector_payloads={"c1": {"text_hash": "a"}},
    )
    report = verify_post_index(stores, version_id="v1")
    assert report.ok is False
    assert any("chunk id mismatch" in a.reason for a in report.alerts)


def test_payload_mismatch_alerted() -> None:
    stores = ConsistencyStores(
        metadata_chunk_ids={"v1": ["c1"]},
        vector_chunk_ids={"v1": ["c1"]},
        metadata_payloads={"c1": {"text_hash": "a"}},
        vector_payloads={"c1": {"text_hash": "DIFFERENT"}},
    )
    report = verify_post_index(stores, version_id="v1")
    assert report.ok is False
    assert any("payload mismatch" in a.reason for a in report.alerts)
