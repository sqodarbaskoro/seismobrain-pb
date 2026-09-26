"""
File: guarded_resources.py
Description: Document preview/download, guarded by real collection access (FR-DOC-03)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-17
Version: 0.3.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import mimetypes
from typing import cast

from fastapi import APIRouter, HTTPException, Request, Response

from seismobrain_api.auth.deps import resolve_scoped_principal
from seismobrain_api.container import AppContainer
from seismobrain_api.document_text import extract_document_text
from seismobrain_core.roles import SystemRole

router = APIRouter(tags=["guarded-resources"])

_PREVIEW_CHAR_LIMIT = 4000


def _container(request: Request) -> AppContainer:
    return cast(AppContainer, request.app.state.container)


def _document_or_404(container: AppContainer, document_id: str) -> dict[str, object]:
    doc = container.collection_access.get_document(document_id)
    if doc is None or doc.get("deleted"):
        raise HTTPException(status_code=404, detail="document not found")
    return doc


def _require_read(request: Request, container: AppContainer, doc: dict[str, object]) -> None:
    """A document is readable by whoever can read its collection — same rule the
    browse endpoint uses (FR-ACL-*: no separate, easily-forgotten grant list)."""
    principal = resolve_scoped_principal(request, required_scope="read")
    if principal.system_role == SystemRole.SYSTEM_ADMIN:
        return
    collection_id = str(doc["collection_id"])
    if not container.collection_access.can_read_collection(principal.user_id, collection_id):
        raise HTTPException(status_code=403, detail="forbidden")


@router.get("/documents/{document_id}/preview")
def preview(document_id: str, request: Request) -> dict[str, object]:
    container = _container(request)
    doc = _document_or_404(container, document_id)
    _require_read(request, container, doc)
    meta = doc["_meta"]
    object_key = str(doc.get("object_key") or "")
    filename = str(getattr(meta, "source_path", "") or getattr(meta, "title", document_id))
    text = ""
    best_effort = True
    if object_key:
        try:
            raw = container.object_store.get(object_key)
            text, best_effort = extract_document_text(filename, raw)
        except (FileNotFoundError, KeyError):
            text = ""
            best_effort = True
    truncated = len(text) > _PREVIEW_CHAR_LIMIT
    return {
        "id": document_id,
        "title": getattr(meta, "title", document_id),
        "doc_type": getattr(meta, "doc_type", ""),
        "text": text[:_PREVIEW_CHAR_LIMIT],
        "truncated": truncated,
        "best_effort": best_effort,
    }


@router.get("/documents/{document_id}/download")
def download(document_id: str, request: Request) -> Response:
    container = _container(request)
    doc = _document_or_404(container, document_id)
    _require_read(request, container, doc)
    object_key = str(doc.get("object_key") or "")
    if not object_key:
        raise HTTPException(status_code=404, detail="no stored file for this document")
    try:
        raw = container.object_store.get(object_key)
    except (FileNotFoundError, KeyError) as exc:
        raise HTTPException(status_code=404, detail="stored file missing") from exc
    meta = doc["_meta"]
    filename = str(getattr(meta, "source_path", "") or getattr(meta, "title", document_id))
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    return Response(
        content=raw,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/citations/{evidence_id}")
def citation(evidence_id: str, request: Request) -> dict[str, str]:
    container = _container(request)
    document_id = container.document_access.document_for_evidence(evidence_id)
    if document_id is None:
        raise HTTPException(status_code=404, detail="not found")
    doc = _document_or_404(container, document_id)
    _require_read(request, container, doc)
    return {"id": evidence_id, "document_id": document_id}


@router.get("/evidence-snapshots/{snapshot_id}")
def snapshot(snapshot_id: str, request: Request) -> dict[str, str]:
    container = _container(request)
    document_id = container.document_access.document_for_snapshot(snapshot_id)
    if document_id is None:
        raise HTTPException(status_code=404, detail="not found")
    doc = _document_or_404(container, document_id)
    _require_read(request, container, doc)
    return {"id": snapshot_id, "document_id": document_id}
