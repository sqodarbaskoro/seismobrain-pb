"""
File: index_alias.py
Description: Physical collection naming and active alias cut-over (FR-IDX-01)
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

from qdrant_client.http import models as qm

from seismobrain_adapters.vector.qdrant_base import QdrantVectorStoreBase

ACTIVE_ALIAS = "seismobrain_chunks_active"


def physical_collection_name(version: int) -> str:
    if version < 1:
        raise ValueError("index version must be >= 1")
    return f"seismobrain_chunks_v{version}"


def set_active_alias(store: QdrantVectorStoreBase, physical_name: str) -> None:
    """Point seismobrain_chunks_active at the given physical collection."""
    ops: list[qm.CreateAliasOperation | qm.DeleteAliasOperation] = []
    existing = store.client.get_aliases().aliases
    for alias in existing:
        if alias.alias_name == ACTIVE_ALIAS:
            ops.append(
                qm.DeleteAliasOperation(
                    delete_alias=qm.DeleteAlias(alias_name=ACTIVE_ALIAS)
                )
            )
            break
    ops.append(
        qm.CreateAliasOperation(
            create_alias=qm.CreateAlias(
                collection_name=physical_name, alias_name=ACTIVE_ALIAS
            )
        )
    )
    store.client.update_collection_aliases(change_aliases_operations=ops)


def resolve_active_collection(store: QdrantVectorStoreBase) -> str | None:
    """Return the physical collection behind the active alias, if any."""
    for alias in store.client.get_aliases().aliases:
        if alias.alias_name == ACTIVE_ALIAS:
            return str(alias.collection_name)
    return None
