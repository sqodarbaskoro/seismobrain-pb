"""
File: research_routes.py
Description: Research plan SSE streaming and enable audit (FR-AGT-05/06)
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

import json
from collections.abc import Iterator
from typing import Any, cast

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from seismobrain_api.auth.deps import require_admin, resolve_principal
from seismobrain_api.container import AppContainer
from seismobrain_core.research_planner import plan_research

router = APIRouter(prefix="/api/v1", tags=["research"])


def _container(request: Request) -> AppContainer:
    return cast(AppContainer, request.app.state.container)


class ResearchStreamBody(BaseModel):
    question: str = Field(min_length=1)
    workspace_id: str


class EnableResearchBody(BaseModel):
    enabled: bool = True


def _sse(event_id: str, event: str, data: dict[str, Any]) -> str:
    return f"id: {event_id}\nevent: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/research/stream")
def research_stream(body: ResearchStreamBody, request: Request) -> StreamingResponse:
    resolve_principal(request)  # any authenticated user; raises 401 if not
    catalog = _container(request).admin_catalog
    workspace = catalog.workspaces.get(body.workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="workspace not found")
    if not workspace.research_enabled:
        raise HTTPException(status_code=403, detail="research disabled")

    frozen = plan_research(body.question)

    def events() -> Iterator[bytes]:
        yield _sse(
            "1",
            "plan",
            {
                "sub_queries": [
                    {"id": s.id, "text": s.text} for s in frozen.plan.sub_queries
                ]
            },
        ).encode()
        for i, sq in enumerate(frozen.plan.sub_queries, start=1):
            yield _sse(
                str(i + 1),
                "progress",
                {"sub_query_id": sq.id, "status": "retrieving", "index": i},
            ).encode()
        yield _sse(
            str(len(frozen.plan.sub_queries) + 2),
            "progress",
            {"status": "complete"},
        ).encode()

    return StreamingResponse(events(), media_type="text/event-stream")


@router.post("/admin/workspaces/{workspace_id}/research")
def set_research_enabled(
    workspace_id: str, body: EnableResearchBody, request: Request
) -> dict[str, object]:
    principal = require_admin(request)
    actor = principal.user_id
    catalog = _container(request).admin_catalog
    if workspace_id not in catalog.workspaces:
        raise HTTPException(status_code=404, detail="workspace not found")
    if body.enabled:
        record = catalog.enable_research(workspace_id, actor=actor)
    else:
        record = catalog.workspaces[workspace_id]
        record.research_enabled = False
        catalog.append_audit(
            action="workspace.research.disable", actor=actor, detail=workspace_id
        )
    return {"id": record.id, "research_enabled": record.research_enabled}
