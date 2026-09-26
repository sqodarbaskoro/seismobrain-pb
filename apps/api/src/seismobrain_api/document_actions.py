"""
File: document_actions.py
Description: Bulk document actions against the real document catalog, with audit (FR-DOC-09)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-18
Version: 0.3.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from seismobrain_api.admin_catalog import AdminCatalog
    from seismobrain_api.collection_access import InMemoryCollectionAccessStore
    from seismobrain_api.search_index import InMemorySearchIndex
    from seismobrain_api.sqlite_admin_catalog import SqliteAdminCatalog

_KNOWN_ACTIONS = frozenset({"move", "retag", "delete", "reindex"})


@dataclass
class BulkDocumentStore:
    """Stateless coordinator: mutates the real document catalog, then audits.

    Deliberately holds no document state of its own — an earlier version kept a
    separate in-memory document dict that real uploads never populated, so bulk
    actions on genuinely uploaded documents always 404'd. This operates on
    `collection_access`'s catalog, the same one browse/upload use.
    """

    def bulk_action(
        self,
        *,
        collection_access: InMemoryCollectionAccessStore,
        admin_catalog: AdminCatalog | SqliteAdminCatalog,
        search_index: InMemorySearchIndex,
        document_ids: list[str],
        action: str,
        actor: str,
        target_collection_id: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        if action not in _KNOWN_ACTIONS:
            raise ValueError(f"unknown action: {action}")
        if action == "move" and not target_collection_id:
            raise ValueError("target_collection_id required")

        touched = 0
        for doc_id in document_ids:
            if collection_access.get_document(doc_id) is None:
                raise KeyError(doc_id)
            if action == "move":
                assert target_collection_id is not None
                collection_access.move_document(doc_id, target_collection_id)
                search_index.update_document_collection(doc_id, target_collection_id)
            elif action == "retag":
                collection_access.retag_document(doc_id, tags or [])
            elif action == "delete":
                collection_access.delete_document(doc_id)
            elif action == "reindex":
                collection_access.mark_needs_reindex(doc_id)
            touched += 1

        admin_catalog.append_audit(
            action=f"documents.bulk.{action}",
            actor=actor,
            detail=f"{touched} document(s): {', '.join(document_ids)}",
        )
        return {"action": action, "count": touched}
