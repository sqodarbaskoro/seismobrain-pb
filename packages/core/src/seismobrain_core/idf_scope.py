"""
File: idf_scope.py
Description: Tenant-scoped IDF corpus filter resolution (FR-RET-12)
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

from enum import StrEnum


class IdfScope(StrEnum):
    TENANT = "tenant"
    WORKSPACE = "workspace"


def resolve_idf_corpus_filter(
    *,
    tenant_id: str,
    workspace_id: str,
    scope: IdfScope = IdfScope.TENANT,
    workspace_point_count: int = 0,
) -> dict[str, str]:
    """IDF corpus MUST stay within the tenant security boundary.

    Workspace scope falls back to tenant when the workspace corpus is empty.
    """
    if not tenant_id:
        raise ValueError("tenant_id required for IDF corpus filter")
    if scope is IdfScope.WORKSPACE and workspace_point_count > 0:
        return {"tenant_id": tenant_id, "workspace_id": workspace_id}
    return {"tenant_id": tenant_id}
