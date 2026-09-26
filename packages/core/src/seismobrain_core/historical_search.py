"""
File: historical_search.py
Description: Explicit audited historical search mode (FR-RET-07)
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
from datetime import date
from typing import Protocol

from seismobrain_core.authorization_guard import CachingAuthorizationGuard
from seismobrain_core.query_builder import HardFilter


@dataclass(frozen=True, slots=True)
class HistoricalScope:
    document_ids: frozenset[str]
    from_date: str
    to_date: str

    def contains_date(self, value: str) -> bool:
        return self.from_date <= value <= self.to_date


@dataclass(frozen=True, slots=True)
class HistoricalHit:
    document_id: str
    version_id: str
    version_date: str
    score: float


@dataclass(frozen=True, slots=True)
class LabelledHistoricalHit:
    document_id: str
    version_id: str
    version_date: str
    score: float
    citation_label: str


class HistoricalAuthzStore(Protocol):
    def check_read(self, user_id: str, document_id: str) -> bool: ...

    def resource_acl_epoch(self, document_id: str) -> int: ...

    def principal_authz_epoch(self, user_id: str) -> int: ...


@dataclass
class HistoricalAuditLog:
    entries: list[dict[str, object]] = field(default_factory=list)

    def record(self, *, user_id: str, scope: HistoricalScope) -> None:
        self.entries.append(
            {
                "user_id": user_id,
                "document_ids": sorted(scope.document_ids),
                "from": scope.from_date,
                "to": scope.to_date,
            }
        )


def build_historical_hard_filter(
    base: HardFilter,
    scope: HistoricalScope,
) -> HardFilter:
    """Replace is_latest with an explicit version-range filter for historical mode."""
    return HardFilter(
        tenant_id=base.tenant_id,
        workspace_id=base.workspace_id,
        collection_ids=base.collection_ids,
        acl_principals=base.acl_principals,
        require_latest=False,
        metadata={
            **base.metadata,
            "document_ids": sorted(scope.document_ids),
            "version_from": scope.from_date,
            "version_to": scope.to_date,
        },
    )


def guard_historical(
    store: HistoricalAuthzStore,
    *,
    user_id: str,
    scope: HistoricalScope,
    candidates: list[HistoricalHit],
) -> tuple[list[HistoricalHit], dict[str, int]]:
    """Enforce current read permission and permitted historical scope."""
    guard = CachingAuthorizationGuard(store)
    kept: list[HistoricalHit] = []
    drops = {"revoked": 0, "out_of_scope": 0}
    for hit in candidates:
        if not guard.check_read(user_id, hit.document_id):
            drops["revoked"] += 1
            continue
        if hit.document_id not in scope.document_ids:
            drops["out_of_scope"] += 1
            continue
        if not scope.contains_date(hit.version_date):
            drops["out_of_scope"] += 1
            continue
        kept.append(hit)
    return kept, drops


def label_historical_hit(hit: HistoricalHit) -> LabelledHistoricalHit:
    """Label results with version and date for citations."""
    parsed = date.fromisoformat(hit.version_date)
    label = f"v={hit.version_id}; date={parsed.isoformat()}"
    return LabelledHistoricalHit(
        document_id=hit.document_id,
        version_id=hit.version_id,
        version_date=hit.version_date,
        score=hit.score,
        citation_label=label,
    )
