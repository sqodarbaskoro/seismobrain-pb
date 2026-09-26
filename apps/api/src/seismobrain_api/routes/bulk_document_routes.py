"""
File: bulk_document_routes.py
Description: Bulk document action API, write-permission checked per collection (FR-DOC-09)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-18
Version: 0.3.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from seismobrain_api.auth.deps import resolve_principal
from seismobrain_api.container import AppContainer
from seismobrain_core.roles import SystemRole

router = APIRouter(prefix="/api/v1", tags=["documents-bulk"])


def _container(request: Request) -> AppContainer:
    return cast(AppContainer, request.app.state.container)


class BulkActionBody(BaseModel):
    document_ids: list[str] = Field(min_length=1)
    action: str
    target_collection_id: str | None = None
    tags: list[str] = Field(default_factory=list)


def _require_write(
    container: AppContainer, *, user_id: str, system_role: SystemRole, collection_id: str
) -> None:
    if not container.collection_access.can_upload(
        user_id=user_id, collection_id=collection_id, system_role=system_role
    ):
        raise HTTPException(status_code=403, detail="write permission required")


@router.post("/documents/bulk")
def bulk_documents(body: BulkActionBody, request: Request) -> dict[str, Any]:
    container = _container(request)
    principal = resolve_principal(request)

    # Every collection this action touches needs write access — the document's
    # current collection always, and a move's destination too (you're placing the
    # document into that collection's namespace).
    for doc_id in body.document_ids:
        doc = container.collection_access.get_document(doc_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="document not found")
        _require_write(
            container,
            user_id=principal.user_id,
            system_role=principal.system_role,
            collection_id=str(doc["collection_id"]),
        )
    if body.action == "move" and body.target_collection_id:
        _require_write(
            container,
            user_id=principal.user_id,
            system_role=principal.system_role,
            collection_id=body.target_collection_id,
        )

    try:
        return container.document_actions.bulk_action(
            collection_access=container.collection_access,
            admin_catalog=container.admin_catalog,
            search_index=container.search_index,
            document_ids=body.document_ids,
            action=body.action,
            actor=principal.user_id,
            target_collection_id=body.target_collection_id,
            tags=body.tags,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="document not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
