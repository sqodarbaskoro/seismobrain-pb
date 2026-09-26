"""
File: conversations.py
Description: Conversations CRUD and message SSE routes (FR-CHAT-01/02)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-18
Version: 0.6.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterator, Sequence
from typing import Any, cast

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from seismobrain_api.auth.deps import resolve_principal, resolve_scoped_principal
from seismobrain_api.chat_doc_qa import run_conversation_doc_qa
from seismobrain_api.container import AppContainer
from seismobrain_api.conversations import MessageRecord
from seismobrain_core.evidence_snapshot_generation_record import (
    build_generation_record,
    generation_record_as_dict,
    prompt_context_hash,
    store_evidence_snapshots,
)
from seismobrain_core.grounded_prompt import (
    SYSTEM_PROMPT_VERSION,
    EvidencePromptBlock,
    build_grounded_prompt,
)
from seismobrain_core.query_rewrite import guarded_rewrite

router = APIRouter(prefix="/api/v1", tags=["conversations"])


def _container(request: Request) -> AppContainer:
    return cast(AppContainer, request.app.state.container)


def _user_id(request: Request) -> str:
    return resolve_principal(request).user_id


class CreateConversationBody(BaseModel):
    workspace_id: str = "default"
    title: str = "New chat"


class RenameBody(BaseModel):
    title: str = Field(min_length=1)


class MessageBody(BaseModel):
    content: str = Field(min_length=1)
    mode: str = "standard"
    grounding_mode: str = "balanced"
    scope: dict[str, Any] = Field(default_factory=dict)


def _sse(event_id: str, event: str, data: dict[str, Any]) -> str:
    return f"id: {event_id}\nevent: {event}\ndata: {json.dumps(data)}\n\n"


def _history_summary(messages: Sequence[MessageRecord], limit: int = 6) -> str:
    """Condensed prior turns for the grounded prompt (PRD Appendix B)."""
    turns = [m for m in messages if m.role in ("user", "assistant") and m.content]
    return "\n".join(f"{m.role}: {m.content}" for m in turns[-limit:])


@router.post("/conversations", status_code=201)
def create_conversation(body: CreateConversationBody, request: Request) -> dict[str, Any]:
    user_id = _user_id(request)
    record = _container(request).conversations.create(
        user_id=user_id, workspace_id=body.workspace_id, title=body.title
    )
    return {"id": record.id, "title": record.title, "workspace_id": record.workspace_id}


@router.get("/conversations")
def list_conversations(request: Request, q: str = "") -> dict[str, Any]:
    user_id = resolve_scoped_principal(request, required_scope="read").user_id
    items = _container(request).conversations.search(user_id, q=q)
    return {
        "conversations": [
            {"id": c.id, "title": c.title, "workspace_id": c.workspace_id} for c in items
        ]
    }


@router.get("/conversations/{conversation_id}/messages")
def list_messages(conversation_id: str, request: Request) -> dict[str, Any]:
    user_id = resolve_scoped_principal(request, required_scope="read").user_id
    try:
        record = _container(request).conversations.require_owner(conversation_id, user_id)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "id": record.id,
        "title": record.title,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "status": m.status,
                "answer": m.answer,
                "citations": m.citations,
                "refusal_type": m.refusal_type,
            }
            for m in record.messages
        ],
    }


@router.patch("/conversations/{conversation_id}")
def rename_conversation(
    conversation_id: str, body: RenameBody, request: Request
) -> dict[str, Any]:
    user_id = _user_id(request)
    try:
        record = _container(request).conversations.rename(
            conversation_id, user_id, body.title
        )
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"id": record.id, "title": record.title}


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: str, request: Request) -> None:
    user_id = _user_id(request)
    try:
        _container(request).conversations.delete(conversation_id, user_id)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/conversations/{conversation_id}/messages")
def post_message(
    conversation_id: str,
    body: MessageBody,
    request: Request,
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
) -> StreamingResponse:
    user_id = _user_id(request)
    container = _container(request)
    try:
        conv = container.conversations.require_owner(conversation_id, user_id)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    stream_id = f"msgstream:{conversation_id}"
    # Replay path: if Last-Event-ID provided and stream exists, replay.
    if last_event_id is not None:
        replayed = container.event_log.replay(stream_id, last_event_id)

        def replay_gen() -> Iterator[str]:
            if replayed:
                for event in replayed:
                    etype = str(event.payload.get("event", "status"))
                    yield _sse(event.event_id, etype, event.payload.get("data", {}))
                return
            # Stream gone: return finalized assistant message if present.
            finals = [m for m in conv.messages if m.role == "assistant" and m.status == "final"]
            if finals:
                msg = finals[-1]
                yield _sse(
                    "final-persisted",
                    "final",
                    {
                        "id": msg.id,
                        "answer": msg.answer,
                        "citations": msg.citations,
                        "status": "final",
                    },
                )
                return
            yield _sse(
                "interrupted",
                "interrupted",
                {"message_id": None, "retryable": True},
            )

        return StreamingResponse(replay_gen(), media_type="text/event-stream")

    def generate() -> Iterator[str]:
        def emit(event: str, data: dict[str, Any]) -> str:
            eid = container.event_log.append(
                stream_id, {"event": event, "data": data}
            )
            return _sse(eid, event, data)

        yield emit("status", {"stage": "routing"})
        yield emit("status", {"stage": "retrieving"})
        scope_collections = body.scope.get("collections")
        collection_ids = (
            [str(c) for c in scope_collections]
            if isinstance(scope_collections, list)
            else None
        )
        yield emit("status", {"stage": "generating"})
        history = [m.content for m in conv.messages if m.role == "user"]
        history_summary = _history_summary(conv.messages)
        resolved_question = guarded_rewrite(body.content, history=history).query
        msg_id = container.conversations.new_message_id()
        user_msg = MessageRecord(
            id=container.conversations.new_message_id(),
            conversation_id=conversation_id,
            role="user",
            content=body.content,
            status="final",
        )
        container.conversations.add_message(conversation_id, user_id, user_msg)
        conversation_title = container.conversations.require_owner(conversation_id, user_id).title
        yield emit("conversation", {"id": conversation_id, "title": conversation_title})
        started_at = time.monotonic()
        result = run_conversation_doc_qa(
            container,
            question=resolved_question,
            collection_ids=collection_ids,
            history_summary=history_summary,
        )
        latency_ms = (time.monotonic() - started_at) * 1000
        container.analytics.record_usage(route=result.route.value, workspace_id=conv.workspace_id)
        container.analytics.record_latency(latency_ms)
        yield emit(
            "trace",
            {
                "resolved_query": resolved_question,
                "route": result.route.value,
                "collection_ids": collection_ids,
                "evidence_count": len(result.citations),
                "latency_ms": round(latency_ms),
            },
        )
        yield emit("status", {"stage": "verifying"})

        if result.refusal is not None:
            container.analytics.record_refusal(result.refusal.type.value)
            container.analytics.record_unanswered(body.content)
            refusal_payload = {
                "id": msg_id,
                "route": result.route.value,
                "refusal": {
                    "type": result.refusal.type.value,
                    "message": result.refusal.message,
                },
                "status": "final",
                "conversation_title": conversation_title,
            }
            assistant = MessageRecord(
                id=msg_id,
                conversation_id=conversation_id,
                role="assistant",
                content=result.refusal.message,
                status="final",
                route=result.route.value,
                refusal_type=result.refusal.type.value,
                answer=[],
                citations={},
            )
            container.conversations.add_message(conversation_id, user_id, assistant)
            yield emit("refusal", refusal_payload)
            yield emit("final", refusal_payload)
            return

        evidence_text = {
            c.evidence_id: next(
                (
                    h.text
                    for h in container.search_index.query(
                        text=resolved_question, collection_ids=collection_ids
                    )
                    if True
                ),
                c.title,
            )
            for c in result.citations
        }
        # Prefer citation texts from grounding sentences' evidence when available.
        if result.grounding is not None:
            for sent in result.grounding.sentences:
                for eid in sent.evidence_ids:
                    evidence_text.setdefault(eid, sent.text)

        snapshot_uris = store_evidence_snapshots(
            container.evidence_snapshots, evidence_text or {"E1": body.content}
        )
        prompt = build_grounded_prompt(
            question=resolved_question,
            evidence=[
                EvidencePromptBlock(evidence_id=eid, text=text)
                for eid, text in evidence_text.items()
            ]
            or [EvidencePromptBlock(evidence_id="E1", text=body.content)],
            history_summary=history_summary,
        )
        provider_name = "configured"
        model_name = "configured"
        active = container.admin_catalog.list_providers()
        if active:
            provider_name = active[0].kind
            model_name = active[0].models[0] if active[0].models else "configured"
        gen_record = build_generation_record(
            messages=prompt.messages,
            evidence_ids=list(evidence_text.keys()) or ["E1"],
            evidence_uris=snapshot_uris,
            question=resolved_question,
            history_summary=history_summary,
            provider=provider_name,
            model=model_name,
            temperature=0.0,
            seed=42,
            max_output_tokens=1024,
            system_prompt_version=SYSTEM_PROMPT_VERSION,
            prompt_blob_uri=container.evidence_snapshots.put(
                "\n".join(m.content for m in prompt.messages)
            ),
        )
        recomputed = prompt_context_hash(
            messages=prompt.messages,
            evidence_ids=list(evidence_text.keys()) or ["E1"],
            template_version=gen_record.prompt_template_version,
        )
        assert recomputed == gen_record.prompt_context_hash

        answer_parts: list[dict[str, Any]] = []
        citations_out: dict[str, Any] = {}
        if result.grounding is not None:
            for index, sent in enumerate(result.grounding.sentences):
                cite_ids = []
                for eid in sent.evidence_ids:
                    cid = f"C{len(citations_out) + 1}"
                    meta = next(
                        (c for c in result.citations if c.evidence_id == eid), None
                    )
                    citations_out[cid] = {
                        "evidence_id": eid,
                        "title": meta.title if meta else eid,
                        "section": meta.section_path if meta else "",
                        "page": meta.page if meta else None,
                        "extraction_method": meta.extraction_method if meta else "digital",
                        "text": evidence_text.get(eid, meta.title if meta else eid),
                        "relevance": meta.relevance if meta else 1.0,
                    }
                    cite_ids.append(cid)
                support = "supported"
                if result.support is not None and index < len(result.support.delivered):
                    support = result.support.delivered[index]
                sentence = {
                    "index": index,
                    "text": sent.text,
                    "evidence": list(sent.evidence_ids),
                    "support": support,
                }
                yield emit("sentence", sentence)
                answer_parts.append(
                    {
                        "text": sent.text,
                        "citations": cite_ids,
                        "support": support,
                    }
                )
        elif result.answer_text:
            yield emit(
                "sentence",
                {
                    "index": 0,
                    "text": result.answer_text,
                    "evidence": [c.evidence_id for c in result.citations],
                    "support": "supported",
                },
            )
            answer_parts.append(
                {
                    "text": result.answer_text,
                    "citations": [f"C{i+1}" for i, _ in enumerate(result.citations)],
                    "support": "supported",
                }
            )
            for i, cite in enumerate(result.citations):
                citations_out[f"C{i+1}"] = {
                    "evidence_id": cite.evidence_id,
                    "title": cite.title,
                    "section": cite.section_path,
                    "page": cite.page,
                    "extraction_method": cite.extraction_method,
                    "text": evidence_text.get(cite.evidence_id, cite.title),
                    "relevance": cite.relevance,
                }

        if result.citations:
            yield emit(
                "evidence",
                {
                    "items": [
                        {
                            "label": c.evidence_id,
                            "title": c.title,
                            "section_path": c.section_path,
                            "page": c.page,
                            "extraction_method": c.extraction_method,
                            "text": evidence_text.get(c.evidence_id, c.title),
                            "score": c.relevance,
                        }
                        for c in result.citations
                    ]
                },
            )

        assistant = MessageRecord(
            id=msg_id,
            conversation_id=conversation_id,
            role="assistant",
            content=result.answer_text or "",
            status="final",
            route=result.route.value,
            answer=answer_parts,
            citations=citations_out,
            grounding_summary_pre={"supported": len(answer_parts)},
            grounding_summary_final={"supported": len(answer_parts)},
            generation_record=generation_record_as_dict(gen_record),
            evidence_snapshot_uris=dict(snapshot_uris),
        )
        container.conversations.add_message(conversation_id, user_id, assistant)
        final_payload = {
            "id": msg_id,
            "conversation_title": conversation_title,
            "route": result.route.value,
            "answer": assistant.answer,
            "citations": assistant.citations,
            "grounding": {
                "mode": body.grounding_mode,
                "supported": len(answer_parts),
                "removed": 0,
            },
            "generation_record": assistant.generation_record,
            "status": "final",
        }
        yield emit("final", final_payload)

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/conversations/{conversation_id}/messages/{message_id}/stop")
def stop_message(
    conversation_id: str, message_id: str, request: Request
) -> dict[str, Any]:
    user_id = _user_id(request)
    try:
        msg = _container(request).conversations.set_message_status(
            conversation_id, message_id, user_id, "interrupted"
        )
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if msg is None:
        raise HTTPException(status_code=404, detail="message not found")
    return {"id": msg.id, "status": msg.status}


@router.post("/conversations/{conversation_id}/messages/{message_id}/regenerate")
def regenerate_message(
    conversation_id: str, message_id: str, request: Request
) -> dict[str, Any]:
    user_id = _user_id(request)
    store = _container(request).conversations
    try:
        msg = store.get_message(conversation_id, message_id, user_id)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if msg is None or msg.role != "assistant":
        raise HTTPException(status_code=404, detail="message not found")
    new_id = store.new_message_id()
    regenerated = MessageRecord(
        id=new_id,
        conversation_id=conversation_id,
        role="assistant",
        content=msg.content,
        status="final",
        route=msg.route,
        answer=list(msg.answer),
        citations=dict(msg.citations),
        generation_record=dict(msg.generation_record),
        evidence_snapshot_uris=dict(msg.evidence_snapshot_uris),
    )
    store.add_message(conversation_id, user_id, regenerated)
    return {"id": new_id, "status": "final", "answer": regenerated.answer}


@router.get("/conversations/{conversation_id}/messages/{message_id}/copy")
def copy_with_citations(
    conversation_id: str, message_id: str, request: Request
) -> dict[str, Any]:
    user_id = _user_id(request)
    try:
        msg = _container(request).conversations.get_message(
            conversation_id, message_id, user_id
        )
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if msg is None:
        raise HTTPException(status_code=404, detail="message not found")
    lines = []
    for part in msg.answer:
        text = str(part.get("text", ""))
        cites = part.get("citations") or []
        cite_bits = []
        for cid in cites:
            meta = msg.citations.get(str(cid), {})
            title = meta.get("title", cid)
            section = meta.get("section", "")
            page = meta.get("page", "")
            cite_bits.append(f"{title} {section} p.{page}".strip())
        suffix = f" ({'; '.join(cite_bits)})" if cite_bits else ""
        lines.append(text + suffix)
    return {"markdown": "\n\n".join(lines), "format": "markdown"}
