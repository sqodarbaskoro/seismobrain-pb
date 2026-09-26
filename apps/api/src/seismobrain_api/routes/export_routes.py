"""
File: export_routes.py
Description: Conversation export Markdown/PDF endpoints (FR-CHAT-07)
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

from fastapi import APIRouter, HTTPException, Request, Response

from seismobrain_api.container import AppContainer
from seismobrain_api.export import ExportSentence, export_markdown, export_pdf
from seismobrain_core.citation_renderer import CitationMetadata

router = APIRouter(prefix="/api/v1", tags=["export"])


def _container(request: Request) -> AppContainer:
    return cast(AppContainer, request.app.state.container)


@router.get("/conversations/{conversation_id}/messages/{message_id}/export")
def export_message(
    conversation_id: str,
    message_id: str,
    request: Request,
    format: str = "markdown",
) -> Response:
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        raise HTTPException(status_code=401, detail="authentication required")
    store = _container(request).conversations
    try:
        msg = store.get_message(conversation_id, message_id, user_id)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if msg is None:
        raise HTTPException(status_code=404, detail="message not found")

    sentences = [
        ExportSentence(
            text=str(item.get("text", "")),
            evidence_ids=tuple(item.get("evidence_ids") or ()),
        )
        for item in msg.answer
    ]
    if not sentences and msg.content:
        sentences = [ExportSentence(text=msg.content, evidence_ids=())]

    citations: dict[str, CitationMetadata] = {}
    for eid, meta in (msg.citations or {}).items():
        if isinstance(meta, dict):
            citations[eid] = CitationMetadata(
                evidence_id=eid,
                title=str(meta.get("title", eid)),
                section_path=str(meta.get("section_path", "")),
                page=meta.get("page"),
                table_ref=meta.get("table_ref"),
                extraction_method=str(meta.get("extraction_method", "digital")),
            )

    title = f"Message {message_id}"
    if format == "pdf":
        body = export_pdf(title=title, sentences=sentences, citations=citations)
        return Response(content=body, media_type="application/pdf")
    text = export_markdown(title=title, sentences=sentences, citations=citations)
    return Response(content=text, media_type="text/markdown; charset=utf-8")
