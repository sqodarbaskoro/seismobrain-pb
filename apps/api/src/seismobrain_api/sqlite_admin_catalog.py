"""
File: sqlite_admin_catalog.py
Description: SQLite-backed admin catalog for Starter persistence
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-17
Modified: 2026-09-17
Version: 0.2.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import base64
import json
import sqlite3
import time
import uuid
from pathlib import Path

from seismobrain_api.admin_catalog import (
    AuditEntry,
    CollectionRecord,
    ProviderRecord,
    WorkspaceRecord,
)
from seismobrain_core.envelope import EncryptedSecret, EnvelopeCipher


class SqliteAdminCatalog:
    """Persist workspaces, collections, providers, and audit under DATA_DIR."""

    def __init__(self, path: Path) -> None:
        self._path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.workspaces: dict[str, WorkspaceRecord] = {}
        self.collections: dict[str, CollectionRecord] = {}
        self.providers: dict[str, ProviderRecord] = {}
        self.audit: list[AuditEntry] = []
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS workspaces (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    research_enabled INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS collections (
                    id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    acl_json TEXT NOT NULL DEFAULT '[]'
                );
                CREATE TABLE IF NOT EXISTS providers (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    name TEXT NOT NULL,
                    models_json TEXT NOT NULL,
                    base_url TEXT NOT NULL DEFAULT '',
                    locality TEXT NOT NULL DEFAULT 'external',
                    secret_key_id TEXT NOT NULL,
                    secret_nonce_b64 TEXT NOT NULL,
                    secret_ciphertext_b64 TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit (
                    id TEXT PRIMARY KEY,
                    action TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    detail TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
                """
            )
            conn.commit()
        self._load()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    def _load(self) -> None:
        with self._connect() as conn:
            for row in conn.execute("SELECT * FROM workspaces"):
                self.workspaces[row["id"]] = WorkspaceRecord(
                    id=row["id"],
                    name=row["name"],
                    research_enabled=bool(row["research_enabled"]),
                )
            for row in conn.execute("SELECT * FROM collections"):
                self.collections[row["id"]] = CollectionRecord(
                    id=row["id"],
                    workspace_id=row["workspace_id"],
                    name=row["name"],
                    acl=json.loads(row["acl_json"]),
                )
            for row in conn.execute("SELECT * FROM providers"):
                self.providers[row["id"]] = ProviderRecord(
                    id=row["id"],
                    kind=row["kind"],
                    name=row["name"],
                    models=json.loads(row["models_json"]),
                    base_url=row["base_url"],
                    locality=row["locality"],
                    secret=EncryptedSecret(
                        key_id=row["secret_key_id"],
                        nonce=base64.b64decode(row["secret_nonce_b64"]),
                        ciphertext=base64.b64decode(row["secret_ciphertext_b64"]),
                    ),
                )
            for row in conn.execute("SELECT * FROM audit ORDER BY created_at"):
                self.audit.append(
                    AuditEntry(
                        id=row["id"],
                        action=row["action"],
                        actor=row["actor"],
                        detail=row["detail"],
                        created_at=float(row["created_at"]),
                    )
                )

    def append_audit(self, *, action: str, actor: str, detail: str) -> AuditEntry:
        entry = AuditEntry(
            id=str(uuid.uuid4()),
            action=action,
            actor=actor,
            detail=detail,
            created_at=time.time(),
        )
        self.audit.append(entry)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO audit (id, action, actor, detail, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (entry.id, entry.action, entry.actor, entry.detail, entry.created_at),
            )
            conn.commit()
        return entry

    def create_workspace(self, name: str, *, actor: str) -> WorkspaceRecord:
        record = WorkspaceRecord(
            id=str(uuid.uuid4()), name=name, research_enabled=False
        )
        self.workspaces[record.id] = record
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO workspaces (id, name, research_enabled)
                VALUES (?, ?, 0)
                """,
                (record.id, record.name),
            )
            conn.commit()
        self.append_audit(action="workspace.create", actor=actor, detail=name)
        return record

    def enable_research(self, workspace_id: str, *, actor: str) -> WorkspaceRecord:
        record = self.workspaces[workspace_id]
        record.research_enabled = True
        with self._connect() as conn:
            conn.execute(
                "UPDATE workspaces SET research_enabled = 1 WHERE id = ?",
                (workspace_id,),
            )
            conn.commit()
        self.append_audit(
            action="workspace.research.enable",
            actor=actor,
            detail=workspace_id,
        )
        return record

    def create_collection(
        self, *, workspace_id: str, name: str, actor: str
    ) -> CollectionRecord:
        if workspace_id not in self.workspaces:
            raise KeyError("workspace not found")
        record = CollectionRecord(
            id=str(uuid.uuid4()), workspace_id=workspace_id, name=name
        )
        self.collections[record.id] = record
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO collections (id, workspace_id, name, acl_json)
                VALUES (?, ?, ?, '[]')
                """,
                (record.id, record.workspace_id, record.name),
            )
            conn.commit()
        self.append_audit(action="collection.create", actor=actor, detail=name)
        return record

    def set_collection_acl(
        self, collection_id: str, entries: list[dict[str, str]], *, actor: str
    ) -> CollectionRecord:
        collection = self.collections[collection_id]
        collection.acl = list(entries)
        with self._connect() as conn:
            conn.execute(
                "UPDATE collections SET acl_json = ? WHERE id = ?",
                (json.dumps(collection.acl), collection_id),
            )
            conn.commit()
        self.append_audit(
            action="collection.acl.update", actor=actor, detail=collection_id
        )
        return collection

    def create_provider(
        self,
        *,
        kind: str,
        name: str,
        models: list[str],
        api_key: str,
        master_key: str,
        actor: str,
        base_url: str = "",
        locality: str = "external",
    ) -> ProviderRecord:
        sealed = EnvelopeCipher(master_key=master_key, key_id="k1").encrypt(
            api_key.encode()
        )
        record = ProviderRecord(
            id=str(uuid.uuid4()),
            kind=kind,
            name=name,
            models=list(models),
            secret=sealed,
            base_url=base_url,
            locality=locality,
        )
        self.providers[record.id] = record
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO providers (
                    id, kind, name, models_json, base_url, locality,
                    secret_key_id, secret_nonce_b64, secret_ciphertext_b64
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.kind,
                    record.name,
                    json.dumps(record.models),
                    record.base_url,
                    record.locality,
                    sealed.key_id,
                    base64.b64encode(sealed.nonce).decode(),
                    base64.b64encode(sealed.ciphertext).decode(),
                ),
            )
            conn.commit()
        self.append_audit(action="provider.create", actor=actor, detail=name)
        return record

    def update_provider(
        self,
        provider_id: str,
        *,
        kind: str,
        name: str,
        models: list[str],
        master_key: str,
        actor: str,
        base_url: str = "",
        locality: str = "external",
        api_key: str | None = None,
    ) -> ProviderRecord | None:
        record = self.providers.get(provider_id)
        if record is None:
            return None
        record.kind = kind
        record.name = name
        record.models = list(models)
        record.base_url = base_url
        record.locality = locality
        if api_key:
            record.secret = EnvelopeCipher(
                master_key=master_key, key_id="k1"
            ).encrypt(api_key.encode())
        sealed = record.secret
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE providers SET
                    kind = ?, name = ?, models_json = ?, base_url = ?, locality = ?,
                    secret_key_id = ?, secret_nonce_b64 = ?, secret_ciphertext_b64 = ?
                WHERE id = ?
                """,
                (
                    record.kind,
                    record.name,
                    json.dumps(record.models),
                    record.base_url,
                    record.locality,
                    sealed.key_id,
                    base64.b64encode(sealed.nonce).decode(),
                    base64.b64encode(sealed.ciphertext).decode(),
                    provider_id,
                ),
            )
            conn.commit()
        self.append_audit(action="provider.update", actor=actor, detail=name)
        return record

    def delete_provider(self, provider_id: str, *, actor: str) -> bool:
        record = self.providers.pop(provider_id, None)
        if record is None:
            return False
        with self._connect() as conn:
            conn.execute("DELETE FROM providers WHERE id = ?", (provider_id,))
            conn.commit()
        self.append_audit(
            action="provider.delete", actor=actor, detail=record.name
        )
        return True

    def list_providers(self) -> list[ProviderRecord]:
        return list(self.providers.values())

    def get_provider(self, provider_id: str) -> ProviderRecord | None:
        return self.providers.get(provider_id)
