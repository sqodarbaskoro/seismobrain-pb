"""
File: qdrant_server.py
Description: Qdrant server VectorStore adapter for Team/Production tiers
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

from qdrant_client import QdrantClient

from seismobrain_adapters.vector.qdrant_base import QdrantVectorStoreBase


class QdrantServerVectorStore(QdrantVectorStoreBase):
    """Team-tier VectorStore talking to a Qdrant server over HTTP."""

    def __init__(self, url: str, api_key: str | None = None) -> None:
        client = QdrantClient(url=url, api_key=api_key)
        super().__init__(client, create_payload_indexes=True)
