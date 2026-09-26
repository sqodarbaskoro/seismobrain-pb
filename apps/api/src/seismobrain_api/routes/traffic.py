"""
File: traffic.py
Description: Chat and upload stub routes with rate limits (SEC-10)
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

from typing import cast

from fastapi import APIRouter, HTTPException, Request

from seismobrain_api.container import AppContainer
from seismobrain_api.rate_limit import enforce_limit

router = APIRouter(tags=["traffic"])


def _container(request: Request) -> AppContainer:
    return cast(AppContainer, request.app.state.container)


def _user_id(request: Request) -> str:
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        raise HTTPException(status_code=401, detail="authentication required")
    return user_id


@router.post("/chat")
def chat(request: Request) -> dict[str, str]:
    container = _container(request)
    user_id = _user_id(request)
    enforce_limit(
        container,
        key=f"chat:user:{user_id}",
        limit=container.settings.chat_rate_limit_per_min,
        window_seconds=60,
    )
    return {"status": "ok"}


@router.post("/uploads")
def uploads(request: Request) -> dict[str, str]:
    container = _container(request)
    user_id = _user_id(request)
    enforce_limit(
        container,
        key=f"upload:user:{user_id}",
        limit=container.settings.upload_rate_limit_per_hour,
        window_seconds=3600,
    )
    return {"status": "ok"}
