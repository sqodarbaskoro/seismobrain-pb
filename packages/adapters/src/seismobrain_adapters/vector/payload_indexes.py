"""
File: payload_indexes.py
Description: Required Qdrant payload indexes per PRD §9.2 / FR-IDX-07
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


@dataclass(frozen=True, slots=True)
class PayloadIndexSpec:
    data_type: str
    is_tenant: bool = False


# PRD §9.2 payload_indexes (custom.* deferred until workspace schema exists).
REQUIRED_PAYLOAD_INDEXES: dict[str, PayloadIndexSpec] = {
    "tenant_id": PayloadIndexSpec("keyword", is_tenant=True),
    "workspace_id": PayloadIndexSpec("keyword"),
    "collection_id": PayloadIndexSpec("keyword"),
    "document_id": PayloadIndexSpec("keyword"),
    "version_id": PayloadIndexSpec("keyword"),
    "acl": PayloadIndexSpec("keyword"),
    "is_latest": PayloadIndexSpec("bool"),
    "doc_type": PayloadIndexSpec("keyword"),
    "tags": PayloadIndexSpec("keyword"),
    "effective_date": PayloadIndexSpec("datetime"),
    "chunk_type": PayloadIndexSpec("keyword"),
    "extraction_method": PayloadIndexSpec("keyword"),
    "pipeline_version": PayloadIndexSpec("keyword"),
    "text_hash": PayloadIndexSpec("keyword"),
}
