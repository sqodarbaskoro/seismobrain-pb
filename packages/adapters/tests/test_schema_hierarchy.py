"""
File: test_schema_hierarchy.py
Description: Tenant→Workspace→Collection→Document→Version schema and migrations
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

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from testcontainers.community.postgres import PostgresContainer

from seismobrain_adapters.metadata.migrations import upgrade_head

_POSTGRES_IMAGE = "postgres:16.10-alpine"
_REQUIRED_TABLES = {
    "tenants",
    "workspaces",
    "collections",
    "documents",
    "document_versions",
}


def _normalize_postgres_url(url: str) -> str:
    parsed = make_url(url)
    if parsed.drivername in {"postgresql", "postgresql+psycopg2"}:
        parsed = parsed.set(drivername="postgresql+psycopg")
    return parsed.render_as_string(hide_password=False)


def _assert_hierarchy(database_url: str) -> None:
    upgrade_head(database_url)
    engine = create_engine(database_url, future=True)
    tables = set(inspect(engine).get_table_names())
    assert _REQUIRED_TABLES.issubset(tables)

    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO tenants (id, name, settings) VALUES ('t1', 'Acme', '{}')")
        )
        conn.execute(
            text(
                "INSERT INTO workspaces "
                "(id, tenant_id, name, grounding_mode, egress_policy, research_enabled, "
                "custom_fields_schema) "
                "VALUES ('w1', 't1', 'Main', 'standard', 'allow', :research, '{}')"
            ),
            {"research": False},
        )
        conn.execute(
            text(
                "INSERT INTO collections "
                "(id, workspace_id, name, path_template, description) "
                "VALUES ('c1', 'w1', 'Docs', '{title}', 'desc')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO documents "
                "(id, collection_id, logical_key, title, status, current_version_id, deleted_at) "
                "VALUES ('d1', 'c1', 'doc-1', 'Title', 'active', NULL, NULL)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO document_versions "
                "(id, document_id, version_no, sha256, size, mime, storage_uri, "
                "rendition_uri, tree_uri, parser_version, pipeline_version, is_latest) "
                "VALUES ('v1', 'd1', 1, 'abc', 10, 'application/pdf', 's3://x', "
                "NULL, NULL, 'p1', 'pipe1', :latest)"
            ),
            {"latest": True},
        )
        conn.execute(
            text("UPDATE documents SET current_version_id = 'v1' WHERE id = 'd1'")
        )
        row = conn.execute(
            text(
                "SELECT d.id, w.tenant_id, c.workspace_id, v.version_no "
                "FROM documents d "
                "JOIN collections c ON c.id = d.collection_id "
                "JOIN workspaces w ON w.id = c.workspace_id "
                "JOIN document_versions v ON v.id = d.current_version_id "
                "WHERE d.id = 'd1'"
            )
        ).one()
        assert row == ("d1", "t1", "w1", 1)


def test_hierarchy_migration_sqlite(tmp_path: Path) -> None:
    db = tmp_path / "meta.db"
    _assert_hierarchy(f"sqlite+pysqlite:///{db}")


@pytest.fixture(scope="module")
def postgres_url() -> Iterator[str]:
    with PostgresContainer(_POSTGRES_IMAGE) as container:
        yield _normalize_postgres_url(container.get_connection_url())


def test_hierarchy_migration_postgres(postgres_url: str) -> None:
    _assert_hierarchy(postgres_url)
