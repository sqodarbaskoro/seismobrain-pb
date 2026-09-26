"""
File: collection_access.py
Description: In-memory collection read/write grants and document catalog (FR-DOC-01/03)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-18
Version: 0.4.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field, replace
from pathlib import Path

from seismobrain_core.core_metadata import CoreMetadata
from seismobrain_core.roles import (
    RoleAction,
    SystemRole,
    WorkspaceRole,
    role_allows,
)


@dataclass
class InMemoryCollectionAccessStore:
    """Tracks workspace role, collection grants, and a browseable document catalog.

    The catalog (`_documents`) optionally write-through persists to SQLite via
    `db_path` — Starter restarts otherwise lose every uploaded document, since this
    store is the only place ingest ever records them (T7.29). ACL grants stay
    in-memory-only; Starter rebuilds those from `catalog.db` on every boot via
    `hydrate_collection_access()`.
    """

    _workspace_roles: dict[tuple[str, str], WorkspaceRole] = field(default_factory=dict)
    _write_grants: set[tuple[str, str]] = field(default_factory=set)
    _read_grants: set[tuple[str, str]] = field(default_factory=set)
    _collection_workspace: dict[str, str] = field(default_factory=dict)
    _documents: dict[str, dict[str, object]] = field(default_factory=dict)
    db_path: Path | None = None

    def __post_init__(self) -> None:
        if self.db_path is None:
            return
        with self._connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS documents (id TEXT PRIMARY KEY, data TEXT NOT NULL)"
            )
            conn.commit()
            for (data,) in conn.execute("SELECT data FROM documents"):
                doc = self._decode(json.loads(data))
                self._documents[str(doc["id"])] = doc

    def _connect(self) -> sqlite3.Connection:
        assert self.db_path is not None
        return sqlite3.connect(self.db_path)

    @staticmethod
    def _decode(row: dict[str, object]) -> dict[str, object]:
        """Inverse of `_persist`'s row shape. `list_documents`/`get_document` read
        display fields off `_meta`, never the flattened top-level keys, so those are
        rebuilt from `meta.to_public_dict()` to stay exactly in sync with it."""
        meta_row = row["meta"]
        assert isinstance(meta_row, dict)
        tags = meta_row.get("tags")
        meta = CoreMetadata(
            title=str(meta_row.get("title", "")),
            doc_type=str(meta_row.get("doc_type", "")),
            revision=str(meta_row.get("revision", "")),
            effective_date=str(meta_row.get("effective_date", "")),
            author=str(meta_row.get("author", "")),
            language=str(meta_row.get("language", "")),
            tags=tuple(str(t) for t in tags) if isinstance(tags, list) else (),
            source_path=str(meta_row.get("source_path", "")),
        )
        return {
            "id": row["id"],
            "collection_id": row["collection_id"],
            **meta.to_public_dict(),
            "tag": row["tag"],
            "source_path": meta.source_path,
            "object_key": row["object_key"],
            "deleted": row["deleted"],
            "needs_reindex": row["needs_reindex"],
            "_meta": meta,
        }

    def _persist(self, document_id: str) -> None:
        if self.db_path is None:
            return
        doc = self._documents[document_id]
        meta = doc["_meta"]
        assert isinstance(meta, CoreMetadata)
        row = {
            "id": doc["id"],
            "collection_id": doc["collection_id"],
            "tag": doc["tag"],
            "object_key": doc["object_key"],
            "deleted": doc["deleted"],
            "needs_reindex": doc["needs_reindex"],
            "meta": {**meta.to_public_dict(), "source_path": meta.source_path},
        }
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO documents (id, data) VALUES (?, ?)",
                (document_id, json.dumps(row)),
            )
            conn.commit()

    def set_workspace_role(
        self, user_id: str, workspace_id: str, role: WorkspaceRole
    ) -> None:
        self._workspace_roles[(user_id, workspace_id)] = role

    def list_workspace_ids(self, user_id: str) -> list[str]:
        """Workspaces this user has any role in — for a self-service "my workspaces"
        listing (unlike the admin console's, which shows every workspace)."""
        return [wid for (uid, wid) in self._workspace_roles if uid == user_id]

    def map_collection(self, collection_id: str, workspace_id: str) -> None:
        self._collection_workspace[collection_id] = workspace_id

    def grant_write(self, user_id: str, collection_id: str) -> None:
        self._write_grants.add((user_id, collection_id))
        self._read_grants.add((user_id, collection_id))

    def grant_read(self, user_id: str, collection_id: str) -> None:
        self._read_grants.add((user_id, collection_id))

    def revoke_read(self, user_id: str, collection_id: str) -> None:
        """Revocation must take effect immediately (PRD non-negotiable) — also drops
        write, since write implies read and a lingering write grant would defeat this."""
        self._read_grants.discard((user_id, collection_id))
        self._write_grants.discard((user_id, collection_id))

    def add_document(
        self,
        *,
        document_id: str,
        collection_id: str,
        title: str,
        doc_type: str = "txt",
        tag: str = "",
        revision: str = "",
        effective_date: str = "",
        author: str = "",
        language: str = "",
        tags: tuple[str, ...] | None = None,
        source_path: str = "",
        object_key: str = "",
    ) -> None:
        resolved_tags = tags if tags is not None else ((tag,) if tag else ())
        meta = CoreMetadata(
            title=title,
            doc_type=doc_type,
            revision=revision,
            effective_date=effective_date,
            author=author,
            language=language,
            tags=resolved_tags,
            source_path=source_path,
        )
        self._documents[document_id] = {
            "id": document_id,
            "collection_id": collection_id,
            **meta.to_public_dict(),
            "tag": resolved_tags[0] if resolved_tags else "",
            "source_path": source_path,
            "object_key": object_key,
            "deleted": False,
            "needs_reindex": False,
            "_meta": meta,
        }
        self._persist(document_id)

    def get_document(self, document_id: str) -> dict[str, object] | None:
        """Raw internal record (collection_id, object_key, _meta, ...) for server-side use."""
        return self._documents.get(document_id)

    def move_document(self, document_id: str, target_collection_id: str) -> None:
        doc = self._documents[document_id]
        doc["collection_id"] = target_collection_id
        self._persist(document_id)

    def retag_document(self, document_id: str, tags: list[str]) -> None:
        doc = self._documents[document_id]
        meta = doc["_meta"]
        assert isinstance(meta, CoreMetadata)
        new_meta = replace(meta, tags=tuple(tags))
        doc["_meta"] = new_meta
        doc["tag"] = tags[0] if tags else ""
        self._persist(document_id)

    def delete_document(self, document_id: str) -> None:
        doc = self._documents[document_id]
        doc["deleted"] = True
        self._persist(document_id)

    def update_document_metadata(self, document_id: str, fields: dict[str, str]) -> None:
        """Apply a metadata correction (FR-META-04) — only plain string core fields;
        tags go through `retag_document`, which also carries the ACL/filter fast path."""
        doc = self._documents[document_id]
        meta = doc["_meta"]
        assert isinstance(meta, CoreMetadata)
        new_meta = replace(
            meta,
            title=fields.get("title", meta.title),
            doc_type=fields.get("doc_type", meta.doc_type),
            revision=fields.get("revision", meta.revision),
            effective_date=fields.get("effective_date", meta.effective_date),
            author=fields.get("author", meta.author),
            language=fields.get("language", meta.language),
        )
        doc["_meta"] = new_meta
        self._persist(document_id)

    def mark_needs_reindex(self, document_id: str) -> None:
        doc = self._documents[document_id]
        doc["needs_reindex"] = True
        self._persist(document_id)

    def can_read_collection(self, user_id: str, collection_id: str) -> bool:
        workspace_id = self._collection_workspace.get(collection_id)
        if workspace_id is None:
            return False
        if self._workspace_roles.get((user_id, workspace_id)) is None:
            return False
        return (user_id, collection_id) in self._read_grants

    def list_collections(self, user_id: str) -> list[str]:
        return sorted(
            collection_id
            for collection_id in self._collection_workspace
            if self.can_read_collection(user_id, collection_id)
        )

    def list_documents(
        self,
        user_id: str,
        collection_id: str,
        *,
        q: str | None = None,
        doc_type: str | None = None,
        tag: str | None = None,
        revision: str | None = None,
        effective_date: str | None = None,
        author: str | None = None,
        language: str | None = None,
        source_path: str | None = None,
        include_source_path: bool = False,
    ) -> list[dict[str, object]]:
        if not self.can_read_collection(user_id, collection_id):
            return []
        results: list[dict[str, object]] = []
        for document in self._documents.values():
            if document["collection_id"] != collection_id or document.get("deleted"):
                continue
            meta = document["_meta"]
            assert isinstance(meta, CoreMetadata)
            if not meta.matches(
                title=q,
                doc_type=doc_type,
                revision=revision,
                effective_date=effective_date,
                author=author,
                language=language,
                tag=tag,
                source_path=source_path,
            ):
                continue
            public = {
                "id": document["id"],
                "collection_id": document["collection_id"],
                **meta.to_public_dict(),
                "tag": document["tag"],
            }
            if include_source_path:
                public["source_path"] = meta.source_path
            results.append(public)
        return sorted(results, key=lambda item: str(item["id"]))
    def can_upload(
        self,
        *,
        user_id: str,
        collection_id: str,
        system_role: SystemRole = SystemRole.USER,
    ) -> bool:
        workspace_id = self._collection_workspace.get(collection_id)
        if workspace_id is None:
            return False
        workspace_role = self._workspace_roles.get((user_id, workspace_id))
        return role_allows(
            system_role=system_role,
            workspace_role=workspace_role,
            action=RoleAction.UPLOAD_EDIT_METADATA,
            collection_grants_write=(user_id, collection_id) in self._write_grants,
        )
