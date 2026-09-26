"""
File: admin_config.py
Description: Effective configuration admin route (FR-ADM-05)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-17
Version: 0.2.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from seismobrain_api.auth.deps import require_admin
from seismobrain_api.effective_config import build_effective_config

router = APIRouter(prefix="/api/v1/admin", tags=["admin-config"])


@router.get("/effective-config")
def effective_config(request: Request) -> dict[str, object]:
    require_admin(request)
    container = request.app.state.container
    return build_effective_config(container.settings)
