"""
File: admin_catalog.py
Description: In-memory admin catalog for workspaces, providers, and audit (M0b)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-17
Version: 0.3.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field

from seismobrain_core.envelope import EncryptedSecret, EnvelopeCipher


@dataclass
class WorkspaceRecord:
    id: str
    name: str
    research_enabled: bool = False


@dataclass
class CollectionRecord:
    id: str
    workspace_id: str
    name: str
    acl: list[dict[str, str]] = field(default_factory=list)


@dataclass
class ProviderRecord:
    id: str
    kind: str
    name: str
    models: list[str]
    secret: EncryptedSecret
    base_url: str = ""
    locality: str = "external"


@dataclass
class AuditEntry:
    id: str
    action: str
    actor: str
    detail: str
    created_at: float


@dataclass
class AdminCatalog:
    workspaces: dict[str, WorkspaceRecord] = field(default_factory=dict)
    collections: dict[str, CollectionRecord] = field(default_factory=dict)
    providers: dict[str, ProviderRecord] = field(default_factory=dict)
    audit: list[AuditEntry] = field(default_factory=list)

    def append_audit(self, *, action: str, actor: str, detail: str) -> AuditEntry:
        entry = AuditEntry(
            id=str(uuid.uuid4()),
            action=action,
            actor=actor,
            detail=detail,
            created_at=time.time(),
        )
        self.audit.append(entry)
        return entry

    def create_workspace(self, name: str, *, actor: str) -> WorkspaceRecord:
        record = WorkspaceRecord(
            id=str(uuid.uuid4()), name=name, research_enabled=False
        )
        self.workspaces[record.id] = record
        self.append_audit(action="workspace.create", actor=actor, detail=name)
        return record

    def enable_research(self, workspace_id: str, *, actor: str) -> WorkspaceRecord:
        record = self.workspaces[workspace_id]
        record.research_enabled = True
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
        self.append_audit(action="collection.create", actor=actor, detail=name)
        return record

    def set_collection_acl(
        self, collection_id: str, entries: list[dict[str, str]], *, actor: str
    ) -> CollectionRecord:
        collection = self.collections[collection_id]
        collection.acl = list(entries)
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
        self.append_audit(action="provider.update", actor=actor, detail=name)
        return record

    def delete_provider(self, provider_id: str, *, actor: str) -> bool:
        record = self.providers.pop(provider_id, None)
        if record is None:
            return False
        self.append_audit(
            action="provider.delete", actor=actor, detail=record.name
        )
        return True

    def list_providers(self) -> list[ProviderRecord]:
        return list(self.providers.values())

    def get_provider(self, provider_id: str) -> ProviderRecord | None:
        return self.providers.get(provider_id)
