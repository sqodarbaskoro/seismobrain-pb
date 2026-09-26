"""
File: metadata_store.py
Description: MetadataStore port (framework-free) for tenant hierarchy persistence
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
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Tenant:
    id: str
    name: str


class MetadataStore(Protocol):
    """Port for metadata persistence. Implementations live in packages/adapters."""

    def create_tenant(self, name: str) -> Tenant:
        """Create a tenant and return it."""

    def get_tenant(self, tenant_id: str) -> Tenant | None:
        """Fetch a tenant by id, or None if missing."""

    def list_tenants(self) -> list[Tenant]:
        """List all tenants."""

    def count_tenants(self) -> int:
        """Return the number of tenants."""
