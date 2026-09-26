"""
File: test_ports.py
Description: Ensure core ports modules are importable and covered
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


def test_tenant_dataclass() -> None:
    tenant = Tenant(id="t1", name="Acme")
    assert tenant.id == "t1"
    assert tenant.name == "Acme"


def test_metadata_store_is_protocol() -> None:
    assert getattr(MetadataStore, "_is_protocol", False) is True
