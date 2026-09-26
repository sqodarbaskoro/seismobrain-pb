"""
File: retrieval.py
Description: Retrieval entrypoint that fails closed without ACL filter (FR-ACL-05)
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

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any


class AclFilterMissingError(ValueError):
    """Raised when retrieval is attempted without a server-built ACL filter."""


@dataclass(frozen=True)
class AclFilter:
    tenant_id: str
    principal_ids: tuple[str, ...]
    require_latest: bool = True


@dataclass(frozen=True)
class RetrievalRequest:
    tenant_id: str
    query_vector: Sequence[float]
    acl_filter: AclFilter | None


def build_acl_filter(
    *,
    tenant_id: str,
    principal_ids: Sequence[str],
    require_latest: bool = True,
) -> AclFilter:
    """Server-side builder for retrieval ACL filters."""
    if not tenant_id:
        raise ValueError("tenant_id required")
    if not principal_ids:
        raise ValueError("principal_ids required")
    return AclFilter(
        tenant_id=tenant_id,
        principal_ids=tuple(principal_ids),
        require_latest=require_latest,
    )


def run_retrieval(
    request: RetrievalRequest,
    *,
    search: Callable[..., list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Execute retrieval; missing ACL filter fails closed."""
    if request.acl_filter is None:
        raise AclFilterMissingError("retrieval requires a server-built ACL filter")
    if request.acl_filter.tenant_id != request.tenant_id:
        raise AclFilterMissingError("ACL filter tenant mismatch")
    return search(
        query_vector=list(request.query_vector),
        acl_filter=request.acl_filter,
    )
