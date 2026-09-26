"""
File: custom_metadata.py
Description: Custom metadata fields per workspace (FR-META-02)
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

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CustomFieldSchema:
    name: str
    field_type: str = "string"
    filterable: bool = True


@dataclass
class CustomMetadataStore:
    schemas: dict[str, list[CustomFieldSchema]] = field(default_factory=dict)
    payload_sync_needed: set[str] = field(default_factory=set)

    def set_schema(self, workspace_id: str, fields: list[CustomFieldSchema]) -> None:
        self.schemas[workspace_id] = list(fields)
        self.payload_sync_needed.add(workspace_id)

    def filterable_payload_fields(self, workspace_id: str) -> list[str]:
        return [f.name for f in self.schemas.get(workspace_id, []) if f.filterable]

    def consume_sync(self, workspace_id: str) -> bool:
        if workspace_id in self.payload_sync_needed:
            self.payload_sync_needed.discard(workspace_id)
            return True
        return False

    def as_public(self, workspace_id: str) -> dict[str, Any]:
        return {
            "fields": [
                {"name": f.name, "type": f.field_type, "filterable": f.filterable}
                for f in self.schemas.get(workspace_id, [])
            ]
        }
