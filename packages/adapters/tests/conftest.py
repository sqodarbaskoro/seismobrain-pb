"""
File: conftest.py
Description: Adapter test fixtures; Colima-compatible testcontainers defaults
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

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from docker.errors import DockerException
from testcontainers.community.minio import MinioContainer

# Pin MinIO on a specific release, never :latest — but MinIO Inc. restricted anonymous
# pulls of older release tags on both Docker Hub and quay.io after their 2025 licensing
# changes, so even a pinned tag can start returning "unauthorized" with no change on
# our side. `minio_container` below skips (not fails) when that happens, since it is a
# registry/licensing access problem, not a defect in the adapters under test.
_MINIO_IMAGE = "quay.io/minio/minio:RELEASE.2024-10-02T17-50-41Z"


def pytest_configure() -> None:
    """Point testcontainers at Colima when present (host socket path ≠ guest path)."""
    colima_sock = Path.home() / ".colima" / "default" / "docker.sock"
    if colima_sock.exists():
        os.environ.setdefault("DOCKER_HOST", f"unix://{colima_sock}")
        # Ryuk must mount the in-VM socket, not the macOS path.
        os.environ.setdefault("TESTCONTAINERS_DOCKER_SOCKET_OVERRIDE", "/var/run/docker.sock")


@pytest.fixture(scope="module")
def minio_container() -> Iterator[MinioContainer]:
    """A real, running MinIO container for S3 adapter tests — skipped (not failed) if
    the pinned image can't be pulled. See the note on `_MINIO_IMAGE` above: this is an
    external registry/licensing access issue, so failing loudly here would report a
    false regression in this repo's own code every single run. If the image becomes
    reachable again — or a maintainer repoints `_MINIO_IMAGE` at a working tag/mirror —
    these tests resume actually exercising the S3 adapter instead of skipping."""
    try:
        container = MinioContainer(_MINIO_IMAGE)
        container.start()
    except DockerException as exc:
        pytest.skip(f"MinIO container unavailable in this environment: {exc}")
    try:
        yield container
    finally:
        container.stop()
