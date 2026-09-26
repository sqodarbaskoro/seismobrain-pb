"""
File: resources.py
Description: Stub resource routes enforcing object-level authorization (SEC-12)
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
from seismobrain_core.object_authz import (
    ObjectAccessError,
    ResourceType,
    require_object_access,
)

router = APIRouter(tags=["resources"])


def _container(request: Request) -> AppContainer:
    return cast(AppContainer, request.app.state.container)


def _actor(request: Request) -> str:
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        raise HTTPException(status_code=401, detail="authentication required")
    return user_id


def _get(request: Request, resource_type: ResourceType, resource_id: str) -> dict[str, str]:
    try:
        require_object_access(
            actor_user_id=_actor(request),
            resource_type=resource_type,
            resource_id=resource_id,
            store=_container(request).object_ownership,
        )
    except ObjectAccessError as exc:
        detail = str(exc)
        if detail == "not found":
            raise HTTPException(status_code=404, detail=detail) from exc
        raise HTTPException(status_code=403, detail=detail) from exc
    return {"id": resource_id, "type": resource_type.value}


@router.get("/conversations/{resource_id}")
def get_conversation(resource_id: str, request: Request) -> dict[str, str]:
    return _get(request, ResourceType.CONVERSATION, resource_id)


@router.get("/messages/{resource_id}")
def get_message(resource_id: str, request: Request) -> dict[str, str]:
    return _get(request, ResourceType.MESSAGE, resource_id)


@router.get("/documents/{resource_id}")
def get_document(resource_id: str, request: Request) -> dict[str, str]:
    return _get(request, ResourceType.DOCUMENT, resource_id)


@router.get("/jobs/{resource_id}")
def get_job(resource_id: str, request: Request) -> dict[str, str]:
    return _get(request, ResourceType.JOB, resource_id)


@router.get("/evidence/{resource_id}")
def get_evidence(resource_id: str, request: Request) -> dict[str, str]:
    return _get(request, ResourceType.EVIDENCE, resource_id)
