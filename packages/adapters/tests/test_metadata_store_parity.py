"""
File: test_metadata_store_parity.py
Description: MetadataStore parity suite: SQLite Starter vs PostgreSQL Team
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
from testcontainers.community.postgres import PostgresContainer

from seismobrain_adapters.metadata.postgres import PostgresMetadataStore
from seismobrain_adapters.metadata.sqlite import SqliteMetadataStore
from seismobrain_core.ports import MetadataStore

# Pin major version per PRD (PostgreSQL ≥ 16); never use :latest.
_POSTGRES_IMAGE = "postgres:16.10-alpine"


def _assert_metadata_store_contract(store: MetadataStore) -> None:
    assert store.count_tenants() == 0
    tenant = store.create_tenant("Acme")
    assert tenant.name == "Acme"
    assert store.count_tenants() == 1
    fetched = store.get_tenant(tenant.id)
    assert fetched is not None
    assert fetched.id == tenant.id
    assert store.list_tenants() == [tenant]
    with pytest.raises(ValueError, match="name"):
        store.create_tenant("  ")


@pytest.fixture(scope="module")
def postgres_url() -> Iterator[str]:
    with PostgresContainer(_POSTGRES_IMAGE) as container:
        yield container.get_connection_url()


@pytest.fixture
def sqlite_store(tmp_path: Path) -> MetadataStore:
    return SqliteMetadataStore(tmp_path / "meta.db")


@pytest.fixture
def postgres_store(postgres_url: str) -> MetadataStore:
    store = PostgresMetadataStore(postgres_url)
    store.reset_schema()
    return store


@pytest.mark.parametrize("store_fixture", ["sqlite_store", "postgres_store"])
def test_metadata_store_parity(store_fixture: str, request: pytest.FixtureRequest) -> None:
    store: MetadataStore = request.getfixturevalue(store_fixture)
    _assert_metadata_store_contract(store)


def test_postgres_store_persists_across_instances(postgres_url: str) -> None:
    first = PostgresMetadataStore(postgres_url)
    first.reset_schema()
    tenant = first.create_tenant("Persisted")
    second = PostgresMetadataStore(postgres_url)
    assert second.get_tenant(tenant.id) == tenant
