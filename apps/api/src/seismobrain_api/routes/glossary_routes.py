"""
File: glossary_routes.py
Description: Glossary and identifier-pattern editor API (FR-ADM-10)
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

from typing import Any, cast

from fastapi import APIRouter, Request
from pydantic import BaseModel

from seismobrain_api.auth.deps import require_admin
from seismobrain_api.container import AppContainer
from seismobrain_api.glossary_store import GlossaryEntry, IdentifierPattern

router = APIRouter(prefix="/api/v1", tags=["glossary"])


def _container(request: Request) -> AppContainer:
    return cast(AppContainer, request.app.state.container)


class GlossaryBody(BaseModel):
    entries: list[dict[str, str]]


class PatternsBody(BaseModel):
    patterns: list[dict[str, str]]


@router.put("/workspaces/{workspace_id}/glossary")
def put_glossary(
    workspace_id: str, body: GlossaryBody, request: Request
) -> dict[str, Any]:
    require_admin(request)
    entries = [
        GlossaryEntry(term=e["term"], expansion=e["expansion"]) for e in body.entries
    ]
    store = _container(request).glossary
    store.set_glossary(workspace_id, entries)
    return store.as_public(workspace_id)


@router.put("/workspaces/{workspace_id}/identifier-patterns")
def put_identifier_patterns(
    workspace_id: str, body: PatternsBody, request: Request
) -> dict[str, Any]:
    require_admin(request)
    patterns = [
        IdentifierPattern(
            name=p["name"],
            pattern=p["pattern"],
            confidence=p.get("confidence", "high"),
        )
        for p in body.patterns
    ]
    store = _container(request).glossary
    store.set_identifier_patterns(workspace_id, patterns)
    return store.as_public(workspace_id)


@router.get("/workspaces/{workspace_id}/glossary")
def get_glossary(workspace_id: str, request: Request) -> dict[str, Any]:
    require_admin(request)
    return _container(request).glossary.as_public(workspace_id)
