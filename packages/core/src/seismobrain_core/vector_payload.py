"""
File: vector_payload.py
Description: Vector point ACL payload contract (FR-ACL-04)
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
from typing import Any

REQUIRED_ACL_PAYLOAD_FIELDS = (
    "tenant_id",
    "workspace_id",
    "collection_id",
    "document_id",
    "version_id",
    "acl",
    "is_latest",
)


@dataclass(frozen=True)
class VectorAclPayload:
    tenant_id: str
    workspace_id: str
    collection_id: str
    document_id: str
    version_id: str
    acl: list[str]
    is_latest: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "workspace_id": self.workspace_id,
            "collection_id": self.collection_id,
            "document_id": self.document_id,
            "version_id": self.version_id,
            "acl": list(self.acl),
            "is_latest": self.is_latest,
        }


def validate_acl_payload(payload: dict[str, Any]) -> VectorAclPayload:
    for field in REQUIRED_ACL_PAYLOAD_FIELDS:
        if field not in payload:
            raise ValueError(f"missing required payload field: {field}")
    acl = payload["acl"]
    if not isinstance(acl, list) or not all(isinstance(item, str) for item in acl):
        raise ValueError("acl must be a list of principal strings")
    if not isinstance(payload["is_latest"], bool):
        raise ValueError("is_latest must be a bool")
    for field in (
        "tenant_id",
        "workspace_id",
        "collection_id",
        "document_id",
        "version_id",
    ):
        if not isinstance(payload[field], str) or not payload[field]:
            raise ValueError(f"{field} must be a non-empty string")
    return VectorAclPayload(
        tenant_id=payload["tenant_id"],
        workspace_id=payload["workspace_id"],
        collection_id=payload["collection_id"],
        document_id=payload["document_id"],
        version_id=payload["version_id"],
        acl=list(acl),
        is_latest=payload["is_latest"],
    )
