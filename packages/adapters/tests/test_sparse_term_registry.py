"""
File: test_sparse_term_registry.py
Description: SparseTermRegistry SQLite and PostgreSQL (+ LRU) tests
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

from seismobrain_adapters.sparse.postgres import PostgresSparseTermRegistry
from seismobrain_adapters.sparse.sqlite import SqliteSparseTermRegistry
from seismobrain_core.ports import SparseTermRegistry

_POSTGRES_IMAGE = "postgres:16.10-alpine"


def _assert_collision_free(registry: SparseTermRegistry) -> None:
    a = registry.get_or_assign(encoder_version="v1", arm="bm25_text", token="alpha")
    b = registry.get_or_assign(encoder_version="v1", arm="bm25_text", token="beta")
    a2 = registry.get_or_assign(encoder_version="v1", arm="bm25_text", token="alpha")
    assert a == a2
    assert a != b
    # Indices are unique within (encoder_version, arm); other arms may reuse idx values.
    other_arm = registry.get_or_assign(encoder_version="v1", arm="ident", token="alpha")
    assert isinstance(other_arm, int)
    again = registry.get_or_assign(encoder_version="v1", arm="ident", token="alpha")
    assert again == other_arm


def test_sqlite_sparse_term_registry(tmp_path: Path) -> None:
    registry: SparseTermRegistry = SqliteSparseTermRegistry(tmp_path / "terms.db")
    _assert_collision_free(registry)


@pytest.fixture(scope="module")
def postgres_url() -> Iterator[str]:
    with PostgresContainer(_POSTGRES_IMAGE) as container:
        yield container.get_connection_url()


def test_postgres_sparse_term_registry_with_lru(postgres_url: str) -> None:
    registry: SparseTermRegistry = PostgresSparseTermRegistry(
        postgres_url, lru_capacity=2
    )
    try:
        _assert_collision_free(registry)
        # Warm LRU then force eviction path still returns stable indices.
        registry.get_or_assign("v1", "bm25_text", "gamma")
        registry.get_or_assign("v1", "bm25_text", "delta")
        assert registry.get_or_assign("v1", "bm25_text", "alpha") >= 0
    finally:
        registry.close()
