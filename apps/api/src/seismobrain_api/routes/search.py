"""
File: search.py
Description: Search API with ACL enforcement and authorization guard (FR-RET-11)
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

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1", tags=["search"])


class SearchRequest(BaseModel):
    query: str
    collection_ids: list[str] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)


def _container(request: Request) -> Any:
    return request.app.state.container


@router.post("/search")
def search(body: SearchRequest, request: Request) -> dict[str, object]:
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        raise HTTPException(status_code=401, detail="authentication required")
    container = _container(request)
    raw = container.search_index.query(
        text=body.query,
        collection_ids=body.collection_ids or None,
        filters=body.filters or None,
    )
    kept: list[dict[str, object]] = []
    dropped = 0
    for hit in raw:
        allowed = container.authorization_guard.check_read(user_id, hit.document_id)
        if not allowed:
            # Fallback to document_access store used by preview/download paths.
            allowed = container.document_access.can_read_document(
                user_id, hit.document_id
            )
        if not allowed:
            dropped += 1
            continue
        kept.append(
            {
                "document_id": hit.document_id,
                "version_id": hit.version_id,
                "text": hit.text,
                "collection_id": hit.collection_id,
                "score": hit.score,
                "metadata": dict(hit.metadata),
            }
        )
    return {
        "query": body.query,
        "scope": {
            "collection_ids": list(body.collection_ids),
            "filters": dict(body.filters),
        },
        "hits": kept,
        "guard": {"dropped": dropped},
    }
