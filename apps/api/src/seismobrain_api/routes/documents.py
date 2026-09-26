"""
File: documents.py
Description: Collection document upload with streamed size limit (FR-DOC-01)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-26
Version: 0.2.1
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import uuid
from pathlib import Path, PurePosixPath
from typing import Annotated, cast

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from seismobrain_api.auth.deps import require_admin, resolve_principal, resolve_scoped_principal
from seismobrain_api.container import AppContainer
from seismobrain_api.ingest_enqueue import enqueue_ingest
from seismobrain_api.upload_limits import UploadTooLargeError, read_upload_limited
from seismobrain_core.ingestion_jobs import IngestionMonitor
from seismobrain_ingest.sample_load import default_corpus_dir

router = APIRouter(prefix="/api/v1", tags=["documents"])

_SAMPLE_SUFFIXES = {".md", ".txt"}


def _container(request: Request) -> AppContainer:
    return cast(AppContainer, request.app.state.container)


def _actor(request: Request) -> str:
    """Used only by the read-only, API-key-enabled routes below (T04.1)."""
    return resolve_scoped_principal(request, required_scope="read").user_id


def _store_and_enqueue(
    container: AppContainer, *, collection_id: str, filename: str, data: bytes
) -> dict[str, str]:
    """Shared by direct upload and the bundled-sample loader below."""
    document_id = str(uuid.uuid4())
    object_key = f"collections/{collection_id}/documents/{document_id}/{filename}"
    container.object_store.put(object_key, data)
    job_id = enqueue_ingest(
        container.job_queue,
        document_id=document_id,
        collection_id=collection_id,
        object_key=object_key,
        filename=filename,
    )
    return {"document_id": document_id, "job_id": job_id, "object_key": object_key}


@router.post("/collections/{collection_id}/documents")
async def upload_document(
    collection_id: str,
    request: Request,
    file: Annotated[UploadFile, File()],
) -> dict[str, str]:
    container = _container(request)
    principal = resolve_principal(request)
    if not container.collection_access.can_upload(
        user_id=principal.user_id,
        collection_id=collection_id,
        system_role=principal.system_role,
    ):
        raise HTTPException(status_code=403, detail="write permission required")

    max_bytes = container.settings.upload_max_bytes
    try:
        data = await read_upload_limited(file.read, max_bytes=max_bytes)
    except UploadTooLargeError as exc:
        raise HTTPException(
            status_code=413,
            detail={
                "code": "upload_too_large",
                "max_bytes": exc.max_bytes,
                "bytes_read": exc.bytes_read,
            },
        ) from exc

    # Client-supplied names may carry path segments; keep only the final component so
    # the object key stays under this document's prefix.
    filename = PurePosixPath((file.filename or "").replace("\\", "/")).name
    if filename in ("", ".."):
        filename = "upload.bin"
    return _store_and_enqueue(
        container, collection_id=collection_id, filename=filename, data=data
    )


@router.get("/collections/{collection_id}/jobs/{job_id}")
def ingest_job_status(collection_id: str, job_id: str, request: Request) -> dict[str, object]:
    """Per-stage ingest progress (parse -> chunk -> index) for the Documents page's own
    upload — anyone who can see the collection, not just admins (unlike the admin
    console's job monitor at GET /api/v1/admin/ingestion/jobs/{id})."""
    container = _container(request)
    user_id = _actor(request)
    if not container.collection_access.can_read_collection(user_id, collection_id):
        raise HTTPException(status_code=403, detail="collection not entitled")
    queue = container.job_queue
    if not isinstance(queue, IngestionMonitor):
        raise HTTPException(status_code=503, detail="Ingestion monitoring is unavailable")
    try:
        job = queue.get_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="job not found") from exc
    if job.collection_id != collection_id:
        raise HTTPException(status_code=404, detail="job not found")
    return {"id": job.id, "stage": job.stage, "status": job.status, "error": job.error}


def _bundled_sample_files(corpus_dir: Path | None = None) -> list[Path]:
    root = corpus_dir or default_corpus_dir()
    if not root.is_dir():
        return []
    return sorted(
        p for p in root.iterdir() if p.is_file() and p.suffix.lower() in _SAMPLE_SUFFIXES
    )


@router.post("/collections/{collection_id}/sample-documents", status_code=201)
def load_sample_documents(collection_id: str, request: Request) -> dict[str, object]:
    """Copy the bundled sample corpus into a collection through the real upload path.

    Admin-only setup helper (guided setup "try it with sample documents"), distinct
    from `seismobrain_ingest.sample_load`'s standalone pipeline smoke test — this
    goes through the same object-store + job-queue path a real upload does, so the
    files are actually searchable afterwards.
    """
    require_admin(request)
    container = _container(request)
    files = _bundled_sample_files()
    if not files:
        raise HTTPException(status_code=404, detail="no bundled sample documents found")
    loaded = [
        _store_and_enqueue(
            container,
            collection_id=collection_id,
            filename=path.name,
            data=path.read_bytes(),
        )
        for path in files
    ]
    return {"documents": loaded}


@router.get("/collections")
def list_collections(request: Request) -> dict[str, list[str]]:
    container = _container(request)
    user_id = _actor(request)
    return {"collections": container.collection_access.list_collections(user_id)}


@router.get("/workspaces")
def list_my_workspaces(request: Request) -> dict[str, object]:
    """Self-service workspace switcher data: only workspaces this caller has a role
    in (unlike GET /admin/workspaces, which lists every workspace for admins), each
    with the collections they can read — with names, unlike the bare ids /collections
    returns, since a switcher needs something a person can actually read."""
    container = _container(request)
    user_id = _actor(request)
    access = container.collection_access
    catalog = container.admin_catalog
    items = []
    for workspace_id in sorted(access.list_workspace_ids(user_id)):
        workspace = catalog.workspaces.get(workspace_id)
        if workspace is None:
            continue
        collections = [
            {"id": c.id, "name": c.name}
            for c in catalog.collections.values()
            if c.workspace_id == workspace_id and access.can_read_collection(user_id, c.id)
        ]
        collections.sort(key=lambda c: c["name"])
        items.append({"id": workspace.id, "name": workspace.name, "collections": collections})
    return {"workspaces": items}


@router.get("/collections/{collection_id}/documents")
def browse_documents(
    collection_id: str,
    request: Request,
    q: str | None = None,
    doc_type: str | None = None,
    tag: str | None = None,
    revision: str | None = None,
    effective_date: str | None = None,
    author: str | None = None,
    language: str | None = None,
) -> dict[str, object]:
    container = _container(request)
    user_id = _actor(request)
    if not container.collection_access.can_read_collection(user_id, collection_id):
        raise HTTPException(status_code=403, detail="collection not entitled")
    documents = container.collection_access.list_documents(
        user_id,
        collection_id,
        q=q,
        doc_type=doc_type,
        tag=tag,
        revision=revision,
        effective_date=effective_date,
        author=author,
        language=language,
    )
    return {"documents": documents}
