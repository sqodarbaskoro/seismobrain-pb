"""
File: duplicate_detection.py
Description: Collection-scoped file duplicate detection (FR-ACL-07)
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


class CollectionDuplicateIndex:
    """Maps (tenant, collection, sha256) → document_id. Never leaks across scopes."""

    def __init__(self) -> None:
        self._by_scope: dict[tuple[str, str, str], str] = {}

    def register(
        self,
        *,
        tenant_id: str,
        collection_id: str,
        sha256: str,
        document_id: str,
    ) -> None:
        self._by_scope[(tenant_id, collection_id, sha256)] = document_id

    def find(
        self,
        *,
        tenant_id: str,
        collection_id: str,
        sha256: str,
    ) -> str | None:
        return self._by_scope.get((tenant_id, collection_id, sha256))
