"""
File: test_object_store.py
Description: ObjectStore filesystem and S3 (MinIO) adapter tests
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-26
Version: 0.2.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from testcontainers.community.minio import MinioContainer

from seismobrain_adapters.object_store.filesystem import FilesystemObjectStore
from seismobrain_adapters.object_store.s3 import S3ObjectStore
from seismobrain_core.ports import ObjectStore


def _assert_object_store_contract(store: ObjectStore) -> None:
    key = "docs/sample.txt"
    assert not store.exists(key)
    store.put(key, b"hello world")
    assert store.exists(key)
    assert store.get(key) == b"hello world"
    assert key in store.list_keys("docs/")
    store.delete(key)
    assert not store.exists(key)


def test_filesystem_object_store(tmp_path: Path) -> None:
    store: ObjectStore = FilesystemObjectStore(tmp_path / "objects")
    _assert_object_store_contract(store)


def test_filesystem_object_store_rejects_sibling_prefix_escape(tmp_path: Path) -> None:
    store = FilesystemObjectStore(tmp_path / "objects")
    with pytest.raises(ValueError, match="escapes"):
        store.put("../objects_evil/x.txt", b"x")
    assert not (tmp_path / "objects_evil").exists()


@pytest.fixture(scope="module")
def minio_store(minio_container: MinioContainer) -> Iterator[S3ObjectStore]:
    cfg = minio_container.get_config()
    store = S3ObjectStore(
        endpoint_url=f"http://{cfg['endpoint']}",
        access_key=str(cfg["access_key"]),
        secret_key=str(cfg["secret_key"]),
        bucket="seismobrain-test",
        region="us-east-1",
    )
    store.ensure_bucket()
    yield store


def test_s3_object_store_against_minio(minio_store: S3ObjectStore) -> None:
    store: ObjectStore = minio_store
    _assert_object_store_contract(store)
