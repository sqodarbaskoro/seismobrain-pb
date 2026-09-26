"""
File: test_sqlite_admin_catalog.py
Description: SQLite admin catalog persists workspaces, collections, providers
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

from pathlib import Path

from seismobrain_api.sqlite_admin_catalog import SqliteAdminCatalog
from seismobrain_core.envelope import EnvelopeCipher


def test_sqlite_admin_catalog_survives_reopen(tmp_path: Path) -> None:
    path = tmp_path / "catalog.db"
    catalog = SqliteAdminCatalog(path)
    ws = catalog.create_workspace("Ops", actor="admin")
    col = catalog.create_collection(
        workspace_id=ws.id, name="manuals", actor="admin"
    )
    catalog.set_collection_acl(
        col.id, [{"principal": "u1", "permission": "read"}], actor="admin"
    )
    provider = catalog.create_provider(
        kind="openai_compatible",
        name="OpenRouter",
        models=["openai/gpt-4o-mini"],
        api_key="sk-secret",
        master_key="b" * 64,
        actor="admin",
        base_url="https://openrouter.ai/api/v1",
        locality="external",
    )

    reopened = SqliteAdminCatalog(path)
    assert ws.id in reopened.workspaces
    assert reopened.workspaces[ws.id].name == "Ops"
    assert col.id in reopened.collections
    assert reopened.collections[col.id].acl == [
        {"principal": "u1", "permission": "read"}
    ]
    loaded = reopened.get_provider(provider.id)
    assert loaded is not None
    assert loaded.base_url == "https://openrouter.ai/api/v1"
    assert loaded.kind == "openai_compatible"
    plain = EnvelopeCipher(master_key="b" * 64, key_id=loaded.secret.key_id).decrypt(
        loaded.secret
    )
    assert plain == b"sk-secret"


def test_sqlite_admin_catalog_update_and_delete_provider(tmp_path: Path) -> None:
    path = tmp_path / "catalog.db"
    catalog = SqliteAdminCatalog(path)
    master = "b" * 64
    provider = catalog.create_provider(
        kind="ollama_vllm",
        name="Ollama",
        models=["llama3.2"],
        api_key="ollama",
        master_key=master,
        actor="admin",
        base_url="http://127.0.0.1:11434/v1",
        locality="local",
    )
    updated = catalog.update_provider(
        provider.id,
        kind="openai_compatible",
        name="OpenRouter",
        models=["openai/gpt-4o-mini"],
        master_key=master,
        actor="admin",
        base_url="https://openrouter.ai/api/v1",
        locality="external",
        api_key="sk-new",
    )
    assert updated is not None
    assert updated.name == "OpenRouter"
    plain = EnvelopeCipher(master_key=master, key_id=updated.secret.key_id).decrypt(
        updated.secret
    )
    assert plain == b"sk-new"

    reopened = SqliteAdminCatalog(path)
    loaded = reopened.get_provider(provider.id)
    assert loaded is not None
    assert loaded.kind == "openai_compatible"
    assert loaded.models == ["openai/gpt-4o-mini"]

    assert catalog.delete_provider(provider.id, actor="admin") is True
    gone = SqliteAdminCatalog(path)
    assert gone.get_provider(provider.id) is None
    assert catalog.delete_provider(provider.id, actor="admin") is False
