"""
File: startup_index_guard.py
Description: Refuse serve on embedding/Qdrant version mismatch (FR-IDX-06)
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

from dataclasses import dataclass

MINIMUM_QDRANT_VERSION = (1, 19, 0)


class StartupIndexError(RuntimeError):
    """Raised when the active index is incompatible with process configuration."""


@dataclass(frozen=True, slots=True)
class ActiveIndexInfo:
    embedding_model: str
    embedding_dimension: int
    qdrant_version: str


@dataclass(frozen=True, slots=True)
class ConfiguredIndexInfo:
    embedding_model: str
    embedding_dimension: int


def parse_qdrant_version(version: str) -> tuple[int, int, int]:
    cleaned = version.lstrip("vV").split("+", 1)[0].split("-", 1)[0]
    parts = cleaned.split(".")
    if len(parts) < 2:
        raise StartupIndexError(f"unparseable Qdrant version: {version}")
    major = int(parts[0])
    minor = int(parts[1])
    patch = int(parts[2]) if len(parts) > 2 else 0
    return major, minor, patch


def assert_startup_index_compatible(
    *,
    configured: ConfiguredIndexInfo,
    active: ActiveIndexInfo,
    minimum_qdrant: tuple[int, int, int] = MINIMUM_QDRANT_VERSION,
) -> None:
    """Fail closed when model, dimension, or Qdrant version is incompatible."""
    qv = parse_qdrant_version(active.qdrant_version)
    if qv < minimum_qdrant:
        raise StartupIndexError(
            f"Qdrant server {active.qdrant_version} older than minimum "
            f"{minimum_qdrant[0]}.{minimum_qdrant[1]}"
        )
    if configured.embedding_model != active.embedding_model:
        raise StartupIndexError(
            f"embedding model mismatch: configured={configured.embedding_model!r} "
            f"active={active.embedding_model!r}"
        )
    if configured.embedding_dimension != active.embedding_dimension:
        raise StartupIndexError(
            f"embedding dimension mismatch: configured={configured.embedding_dimension} "
            f"active={active.embedding_dimension}"
        )
