"""
File: authorization_guard.py
Description: Epoch-keyed AuthorizationGuard against metadata store (FR-ACL-09)
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

from typing import Protocol


class MetadataAuthzStore(Protocol):
    def check_read(self, user_id: str, document_id: str) -> bool: ...

    def resource_acl_epoch(self, document_id: str) -> int: ...

    def principal_authz_epoch(self, user_id: str) -> int: ...


class CachingAuthorizationGuard:
    """
    Re-check every candidate against the metadata store.

    Cache key: (user, principal_authz_epoch, document, resource_acl_epoch).
    """

    def __init__(self, store: MetadataAuthzStore) -> None:
        self._store = store
        self._cache: dict[tuple[str, int, str, int], bool] = {}

    def check_read(self, user_id: str, document_id: str) -> bool:
        principal_epoch = self._store.principal_authz_epoch(user_id)
        resource_epoch = self._store.resource_acl_epoch(document_id)
        key = (user_id, principal_epoch, document_id, resource_epoch)
        if key in self._cache:
            return self._cache[key]
        allowed = self._store.check_read(user_id, document_id)
        self._cache[key] = allowed
        return allowed

    def filter_readable(self, user_id: str, document_ids: list[str]) -> list[str]:
        return [doc_id for doc_id in document_ids if self.check_read(user_id, doc_id)]
