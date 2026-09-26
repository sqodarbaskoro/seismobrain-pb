"""
File: app.py
Description: FastAPI application factory with port DI and router registration
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-17
Version: 0.3.1
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from seismobrain_api.air_gapped import assert_air_gapped_startup
from seismobrain_api.container import AppContainer
from seismobrain_api.routes import (
    admin_analytics,
    admin_audit,
    admin_config,
    admin_ingestion_monitor,
    admin_providers,
    admin_users,
    admin_workspaces,
    api_token_routes,
    auth,
    bulk_document_routes,
    conversations,
    documents,
    export_routes,
    glossary_routes,
    groups,
    guarded_resources,
    health,
    metadata_feedback_routes,
    metrics_routes,
    oidc_routes,
    quarantine_routes,
    research_routes,
    resources,
    search,
    session_routes,
    traffic,
)
from seismobrain_api.security_headers import SecurityHeadersMiddleware
from seismobrain_api.starter_bind import warn_if_starter_exposed
from seismobrain_api.startup_index_guard import assert_startup_index_compatible


def create_e2e_app() -> FastAPI:
    """Ephemeral API for Playwright (no SPA). Uses SB_DATA_DIR when set."""
    import os
    from pathlib import Path

    from seismobrain_adapters.authz.deny import DenyAllAuthorizationGuard
    from seismobrain_adapters.event_log.in_memory import InMemoryEventLog
    from seismobrain_adapters.metadata.sqlite import SqliteMetadataStore
    from seismobrain_adapters.object_store.filesystem import FilesystemObjectStore
    from seismobrain_adapters.queue.in_process import InProcessJobQueue
    from seismobrain_adapters.rate_limit.in_memory import InMemoryRateLimiter
    from seismobrain_api.auth.sqlite_api_tokens import SqliteApiTokenStore
    from seismobrain_api.auth.sqlite_users import SqliteUserStore
    from seismobrain_api.catalog_hydrate import hydrate_collection_access
    from seismobrain_api.config import load_settings
    from seismobrain_api.sqlite_admin_catalog import SqliteAdminCatalog
    from seismobrain_api.starter_ingest import register_starter_ingest, start_ingest_worker
    from seismobrain_core.roles import SystemRole

    settings = load_settings()
    root = Path(os.environ.get("SB_DATA_DIR", "data/e2e"))
    root.mkdir(parents=True, exist_ok=True)
    user_store = SqliteUserStore(root / "users.db")
    if user_store.count() == 0:
        admin = user_store.create(
            email=os.environ.get("E2E_ADMIN_EMAIL", "admin@example.com"),
            name="E2E Admin",
            password=os.environ.get("E2E_ADMIN_PASSWORD", "e2e-admin-pass-12"),
            status="active",
        )
        user_store.set_system_role(admin.id, SystemRole.SYSTEM_ADMIN)
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
    from seismobrain_api.e2e_ingestion import install_ingestion_fixture

    install_ingestion_fixture(app, container)
    return app


def create_app(container: AppContainer) -> FastAPI:
    """Build the API app with DI container and registered routers."""
    assert_air_gapped_startup(air_gapped=container.settings.air_gapped)
    if container.configured_index is not None and container.active_index is not None:
        assert_startup_index_compatible(
            configured=container.configured_index,
            active=container.active_index,
        )
    production = container.settings.environment == "production"
    app = FastAPI(
        title="SeismoBrain API",
        version="0.0.0",
        docs_url=None if production else "/docs",
        redoc_url=None if production else "/redoc",
        openapi_url=None if production else "/openapi.json",
    )
    app.state.container = container
    warn_if_starter_exposed(container.settings)
    app.add_middleware(SecurityHeadersMiddleware)
    app.include_router(health.router)
    app.include_router(metrics_routes.router)
    app.include_router(auth.router)
    app.include_router(documents.router)
    app.include_router(search.router)
    app.include_router(conversations.router)
    app.include_router(export_routes.router)
    app.include_router(research_routes.router)
    app.include_router(quarantine_routes.router)
    app.include_router(bulk_document_routes.router)
    app.include_router(metadata_feedback_routes.router)
    app.include_router(glossary_routes.router)
    app.include_router(groups.router)
    app.include_router(oidc_routes.router)
    app.include_router(api_token_routes.router)
    app.include_router(session_routes.router)
    app.include_router(resources.router)
    app.include_router(traffic.router)
    app.include_router(guarded_resources.router)
    app.include_router(admin_users.router)
    app.include_router(admin_workspaces.router)
    app.include_router(admin_providers.router)
    app.include_router(admin_audit.router)
    app.include_router(admin_ingestion_monitor.router)
    app.include_router(admin_config.router)
    app.include_router(admin_analytics.router)

    if production:

        @app.get("/openapi.json", include_in_schema=False)
        def openapi_json(request: Request) -> JSONResponse:
            if request.headers.get("X-System-Role") != "system_admin":
                raise HTTPException(status_code=403, detail="admin only")
            return JSONResponse(
                get_openapi(
                    title=app.title,
                    version=app.version,
                    routes=app.routes,
                )
            )

    return app
