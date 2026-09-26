"""
File: admin_analytics.py
Description: Admin analytics endpoint (FR-ADM-08)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-18
Version: 0.1.1
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Request

from seismobrain_api.auth.deps import require_admin
from seismobrain_api.container import AppContainer

router = APIRouter(prefix="/api/v1/admin", tags=["admin-analytics"])


@router.get("/analytics")
def analytics(request: Request) -> dict[str, object]:
    # Was unguarded (unlike every sibling /admin/* route) — usage counts, refusal
    # rates, workspace ids and top unanswered questions are not for anonymous callers.
    require_admin(request)
    container = cast(AppContainer, request.app.state.container)
    return container.analytics.snapshot()
