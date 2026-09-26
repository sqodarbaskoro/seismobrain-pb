"""
File: query_builder.py
Description: Three-arm prefetch query builder with identical hard filters (FR-RET-01)
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

from seismobrain_core.retrieval import AclFilterMissingError


@dataclass(frozen=True, slots=True)
class HardFilter:
    tenant_id: str
    workspace_id: str
    collection_ids: tuple[str, ...]
    acl_principals: tuple[str, ...]
    require_latest: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PrefetchArm:
    name: str
    hard_filter: HardFilter


@dataclass(frozen=True, slots=True)
class BuiltQuery:
    text: str
    prefetch: tuple[PrefetchArm, ...]
    root_filter: HardFilter


def build_query(
    *,
    text: str,
    hard_filter: HardFilter | None,
    has_identifiers: bool,
) -> BuiltQuery:
    """Build prefetch arms; hard filter required on every arm and at the root."""
    if hard_filter is None:
        raise AclFilterMissingError("query requires a server-built hard filter")
    if not hard_filter.tenant_id or not hard_filter.acl_principals:
        raise AclFilterMissingError("hard filter incomplete")

    arms: list[PrefetchArm] = [
        PrefetchArm(name="dense", hard_filter=hard_filter),
        PrefetchArm(name="bm25_text", hard_filter=hard_filter),
    ]
    if has_identifiers:
        arms.append(PrefetchArm(name="ident", hard_filter=hard_filter))
    return BuiltQuery(text=text, prefetch=tuple(arms), root_filter=hard_filter)
