"""
File: starter.py
Description: Starter-tier MetadataStore wrapper enforcing single-tenant constraint
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

from seismobrain_core.ports import MetadataStore, Tenant


class StarterSingleTenantMetadataStore:
    """Wraps a MetadataStore and refuses a second tenant (PRD §16.6 / §8.4.4)."""

    def __init__(self, inner: MetadataStore) -> None:
        self._inner = inner

    def create_tenant(self, name: str) -> Tenant:
        if self._inner.count_tenants() >= 1:
            raise ValueError("Starter tier allows a single tenant only")
        return self._inner.create_tenant(name)

    def get_tenant(self, tenant_id: str) -> Tenant | None:
        return self._inner.get_tenant(tenant_id)

    def list_tenants(self) -> list[Tenant]:
        return self._inner.list_tenants()

    def count_tenants(self) -> int:
        return self._inner.count_tenants()
