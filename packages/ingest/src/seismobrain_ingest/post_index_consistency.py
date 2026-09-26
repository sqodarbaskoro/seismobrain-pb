"""
File: post_index_consistency.py
Description: Post-index metadata vs vector consistency check (FR-ING-10)
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

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ConsistencyAlert:
    version_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class ConsistencyReport:
    ok: bool
    alerts: tuple[ConsistencyAlert, ...]


@dataclass
class ConsistencyStores:
    """Minimal metadata + vector views for post-index verification."""

    metadata_chunk_ids: dict[str, list[str]] = field(default_factory=dict)
    metadata_payloads: dict[str, dict[str, Any]] = field(default_factory=dict)
    vector_chunk_ids: dict[str, list[str]] = field(default_factory=dict)
    vector_payloads: dict[str, dict[str, Any]] = field(default_factory=dict)


def verify_post_index(stores: ConsistencyStores, *, version_id: str) -> ConsistencyReport:
    """Compare metadata and vector counts/payloads for one document version."""
    alerts: list[ConsistencyAlert] = []
    meta_ids = sorted(stores.metadata_chunk_ids.get(version_id, []))
    vec_ids = sorted(stores.vector_chunk_ids.get(version_id, []))
    if meta_ids != vec_ids:
        alerts.append(
            ConsistencyAlert(
                version_id=version_id,
                reason=f"chunk id mismatch meta={meta_ids} vector={vec_ids}",
            )
        )
    for chunk_id in set(meta_ids) | set(vec_ids):
        meta_payload = stores.metadata_payloads.get(chunk_id)
        vec_payload = stores.vector_payloads.get(chunk_id)
        if meta_payload != vec_payload:
            alerts.append(
                ConsistencyAlert(
                    version_id=version_id,
                    reason=f"payload mismatch for chunk {chunk_id}",
                )
            )
    return ConsistencyReport(ok=not alerts, alerts=tuple(alerts))
