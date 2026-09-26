"""
File: qdrant_local.py
Description: Qdrant local-mode VectorStore adapter for Starter tier (DATA_DIR/qdrant)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-16
Version: 0.1.1
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from pathlib import Path

from qdrant_client import QdrantClient

from seismobrain_adapters.vector.qdrant_base import QdrantVectorStoreBase


class QdrantLocalVectorStore(QdrantVectorStoreBase):
    """Starter-tier VectorStore using Qdrant local (on-disk) mode under DATA_DIR/qdrant."""

    def __init__(self, data_dir: Path | str) -> None:
        root = Path(data_dir)
        self._path = root / "qdrant"
        self._path.mkdir(parents=True, exist_ok=True)
        client = QdrantClient(path=str(self._path))
        # Local mode ignores payload indexes; Team server creates them.
        super().__init__(client, create_payload_indexes=False)

    @property
    def storage_path(self) -> Path:
        return self._path
