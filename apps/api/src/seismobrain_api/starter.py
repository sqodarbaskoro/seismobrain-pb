"""
File: starter.py
Description: Starter-tier single-process app factory and ASGI entry (T0c.6)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-18
Version: 0.1.4
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI

from seismobrain_adapters.authz.deny import DenyAllAuthorizationGuard
from seismobrain_adapters.event_log.in_memory import InMemoryEventLog
from seismobrain_adapters.evidence.inline import InlineEvidenceSnapshotStore
from seismobrain_adapters.metadata.sqlite import SqliteMetadataStore
from seismobrain_adapters.object_store.filesystem import FilesystemObjectStore
from seismobrain_adapters.queue.in_process import InProcessJobQueue
from seismobrain_adapters.rate_limit.in_memory import InMemoryRateLimiter
from seismobrain_api.app import create_app
from seismobrain_api.auth.sqlite_api_tokens import SqliteApiTokenStore
from seismobrain_api.auth.sqlite_users import SqliteUserStore
from seismobrain_api.catalog_hydrate import hydrate_collection_access
from seismobrain_api.collection_access import InMemoryCollectionAccessStore
from seismobrain_api.config import load_settings
from seismobrain_api.container import AppContainer
from seismobrain_api.search_index import InMemorySearchIndex
from seismobrain_api.spa import default_spa_dist, mount_spa
from seismobrain_api.sqlite_admin_catalog import SqliteAdminCatalog
from seismobrain_api.sqlite_conversations import SqliteConversationStore
from seismobrain_api.starter_bind import warn_if_starter_exposed
from seismobrain_api.starter_ingest import register_starter_ingest, start_ingest_worker


def build_starter_app(
    data_dir: Path | None = None, spa_dir: Path | None = None
) -> FastAPI:
    """Wire Starter adapters and return a FastAPI app bound for loopback use."""
    settings = load_settings()
    warn_if_starter_exposed(settings)
    root = data_dir or Path(os.environ.get("SB_DATA_DIR", "data"))
    root.mkdir(parents=True, exist_ok=True)
    user_store = SqliteUserStore(root / "users.db")
    catalog = SqliteAdminCatalog(root / "catalog.db")
    container = AppContainer(
        settings=settings,
        metadata_store=SqliteMetadataStore(root / "meta.db"),
        job_queue=InProcessJobQueue(root / "jobs"),
        object_store=FilesystemObjectStore(root / "objects"),
        event_log=InMemoryEventLog(),
        rate_limiter=InMemoryRateLimiter(),
        authorization_guard=DenyAllAuthorizationGuard(),
        user_store=user_store,
        admin_catalog=catalog,
        collection_access=InMemoryCollectionAccessStore(db_path=root / "documents.db"),
        search_index=InMemorySearchIndex(db_path=root / "search_index.db"),
        conversations=SqliteConversationStore(root / "conversations.db"),
        evidence_snapshots=InlineEvidenceSnapshotStore(root / "evidence_snapshots.db"),
        api_tokens=SqliteApiTokenStore(root / "api_tokens.db"),
    )
    hydrate_collection_access(
        catalog=catalog,
        access=container.collection_access,
        user_store=user_store,
    )
    register_starter_ingest(container)
    start_ingest_worker(container.job_queue)
    app = create_app(container)
    mount_spa(app, spa_dir if spa_dir is not None else default_spa_dist())
    return app
