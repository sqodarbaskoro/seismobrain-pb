"""
File: metadata_feedback_routes.py
Description: Custom metadata, review sync, and feedback routes (FR-META-02/04, FR-FB-01/02)
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

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from seismobrain_api.auth.deps import require_admin
from seismobrain_api.container import AppContainer
from seismobrain_api.custom_metadata import CustomFieldSchema

router = APIRouter(prefix="/api/v1", tags=["metadata-feedback"])


def _container(request: Request) -> AppContainer:
    return cast(AppContainer, request.app.state.container)


class SchemaBody(BaseModel):
    fields: list[dict[str, Any]]


class ReviewBody(BaseModel):
    document_id: str
    fields: dict[str, str]


class FeedbackBody(BaseModel):
    message_id: str
    rating: str
    reason: str
    comment: str = ""


@router.put("/workspaces/{workspace_id}/custom-metadata")
def set_custom_metadata(workspace_id: str, body: SchemaBody, request: Request) -> dict[str, Any]:
    require_admin(request)
    fields = [
        CustomFieldSchema(
            name=str(f["name"]),
            field_type=str(f.get("type", "string")),
            filterable=bool(f.get("filterable", True)),
        )
        for f in body.fields
    ]
    store = _container(request).custom_metadata
    store.set_schema(workspace_id, fields)
    sync_triggered = store.consume_sync(workspace_id)
    return {**store.as_public(workspace_id), "payload_sync_triggered": sync_triggered}


@router.post("/metadata/review")
def review_metadata(body: ReviewBody, request: Request) -> dict[str, Any]:
    require_admin(request)
    container = _container(request)
    if container.collection_access.get_document(body.document_id) is None:
        raise HTTPException(status_code=404, detail="document not found")
    container.collection_access.update_document_metadata(body.document_id, body.fields)
    container.metadata_reviews[body.document_id] = dict(body.fields)
    container.vector_payload_sync.add(body.document_id)
    return {
        "document_id": body.document_id,
        "fields": body.fields,
        "propagated_to_index": True,
    }


@router.post("/feedback", status_code=201)
def create_feedback(body: FeedbackBody, request: Request) -> dict[str, Any]:
    container = _container(request)
    item = container.feedback.add(
        message_id=body.message_id,
        rating=body.rating,
        reason=body.reason,
        comment=body.comment,
    )
    # Separate from the FeedbackStore above (which backs promote-to-eval-case): this is
    # what GET /api/v1/admin/analytics reads for the admin dashboard's feedback trends.
    container.analytics.record_feedback(rating=body.rating, reason=body.reason or "none")
    return {
        "id": item.id,
        "rating": item.rating,
        "reason": item.reason,
        "comment": item.comment,
    }


@router.post("/feedback/{feedback_id}/promote")
def promote_feedback(feedback_id: str, request: Request) -> dict[str, Any]:
    actor = request.headers.get("X-User-Id") or "curator"
    try:
        return _container(request).feedback.promote(feedback_id, actor=actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="feedback not found") from exc
