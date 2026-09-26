"""
File: test_embedding_cache.py
Description: EmbeddingCache SQLite Starter and bounded Team store tests
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

import sqlite3
from pathlib import Path

from seismobrain_adapters.embedding_cache.bounded import BoundedObjectEmbeddingCache
from seismobrain_adapters.embedding_cache.sqlite import SqliteEmbeddingCache
from seismobrain_adapters.object_store.filesystem import FilesystemObjectStore
from seismobrain_core.ports import EmbeddingCache

_KEY = ("abc123", "model-a", "rev1")
_VEC = [0.1, 0.2, 0.3, 0.4]


def _assert_cache_roundtrip(cache: EmbeddingCache) -> None:
    assert cache.get(*_KEY) is None
    cache.put(*_KEY, vector=_VEC)
    assert cache.get(*_KEY) == _VEC


def test_sqlite_embedding_cache(tmp_path: Path) -> None:
    cache: EmbeddingCache = SqliteEmbeddingCache(tmp_path / "embed.db")
    _assert_cache_roundtrip(cache)


def test_bounded_object_cache_enforces_size_cap(tmp_path: Path) -> None:
    store = FilesystemObjectStore(tmp_path / "objects")
    meta = tmp_path / "embed_meta.db"
    # Cap is tiny so the second vector evicts the first (LRU).
    cache = BoundedObjectEmbeddingCache(
        object_store=store,
        meta_db_path=meta,
        max_bytes=20,
    )
    cache.put("t1", "m", "r", vector=[1.0] * 8)
    assert cache.get("t1", "m", "r") is not None
    cache.put("t2", "m", "r", vector=[2.0] * 8)
    assert cache.get("t2", "m", "r") is not None
    assert cache.get("t1", "m", "r") is None
    assert cache.size_bytes() <= 20


def test_bounded_cache_meta_has_no_vector_column(tmp_path: Path) -> None:
    """Team/Production: metadata holds keys/locations only (no vector blobs)."""
    store = FilesystemObjectStore(tmp_path / "objects")
    meta = tmp_path / "embed_meta.db"
    cache = BoundedObjectEmbeddingCache(
        object_store=store, meta_db_path=meta, max_bytes=10_000
    )
    cache.put(*_KEY, vector=_VEC)
    with sqlite3.connect(meta) as conn:
        cols = [row[1] for row in conn.execute("PRAGMA table_info(embedding_cache)")]
    assert "vector" not in cols
    assert "vector_json" not in cols
    assert "location" in cols
