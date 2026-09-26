"""
File: chat_doc_qa.py
Description: Wire conversations SSE to core run_doc_qa + configured LLM provider
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-17
Modified: 2026-09-18
Version: 0.3.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

from seismobrain_adapters.llm.strategies import (
    AnthropicProvider,
    GeminiProvider,
    OpenAICompatibleProvider,
)
from seismobrain_adapters.models.in_process import InProcessModelGateway
from seismobrain_api.container import AppContainer
from seismobrain_api.provider_test import build_strategy
from seismobrain_core.citation_renderer import CitationMetadata
from seismobrain_core.context_builder import EvidenceItem
from seismobrain_core.doc_qa import DocQaResult, run_doc_qa
from seismobrain_core.envelope import EnvelopeCipher
from seismobrain_core.ports.llm_provider import LLMCompletion, LLMMessage
from seismobrain_core.router import RouteClass
from seismobrain_core.typed_refusals import RefusalType, make_refusal

_LLM_KINDS = frozenset({"openai_compatible", "anthropic", "gemini", "ollama_vllm"})


_ProviderStrategy = OpenAICompatibleProvider | AnthropicProvider | GeminiProvider


def _provider_candidates(
    container: AppContainer,
) -> list[tuple[_ProviderStrategy, str, str]]:
    """Newest providers first so a later working config beats an earlier dead one."""
    records = [
        p
        for p in container.admin_catalog.list_providers()
        if p.kind in _LLM_KINDS and p.models and p.base_url
    ]
    candidates: list[tuple[_ProviderStrategy, str, str]] = []
    for record in reversed(records):
        api_key = (
            EnvelopeCipher(
                master_key=container.settings.master_key, key_id=record.secret.key_id
            )
            .decrypt(record.secret)
            .decode()
        )
        strategy = build_strategy(
            kind=record.kind,
            base_url=record.base_url,
            api_key=api_key,
            transport=container.llm_transport,
        )
        candidates.append((strategy, record.models[0], record.kind))
    return candidates


def run_conversation_doc_qa(
    container: AppContainer,
    *,
    question: str,
    collection_ids: list[str] | None = None,
    history_summary: str = "",
) -> DocQaResult:
    candidates = _provider_candidates(container)
    if not candidates:
        return DocQaResult(
            route=RouteClass.DOC_QA,
            grounding=None,
            citations=(),
            support=None,
            refusal=make_refusal(RefusalType.PROVIDER_ERROR),
            answer_text=None,
        )
    gateway = InProcessModelGateway()

    # Retrieval + rerank are computed once up front (not inside the retrieve/rerank
    # closures) so citation_meta's E-labels can be derived from the exact same
    # relevance-sorted order that context_builder.build_context uses internally —
    # otherwise the two would drift out of sync whenever rerank actually changes an
    # item's relevance, and a citation could point at the wrong chunk's metadata.
    hits = container.search_index.query(text=question, collection_ids=collection_ids)[
        :20
    ]
    hit_by_chunk_id = {
        str(hit.metadata.get("chunk_id") or hit.document_id): hit for hit in hits
    }
    raw_items = [
        EvidenceItem(
            chunk_id=str(hit.metadata.get("chunk_id") or hit.document_id),
            text=hit.text,
            relevance=float(hit.score),
        )
        for hit in hits
    ]
    if raw_items:
        order = gateway.rerank(
            question, [item.text for item in raw_items], model_id="cpu-rerank"
        )
        ranked_items = [
            replace(raw_items[doc_index], relevance=1.0 - (rank / len(order)))
            for rank, doc_index in enumerate(order)
        ]
    else:
        ranked_items = []
    ranked_by_chunk_id = {item.chunk_id: item for item in ranked_items}

    def retrieve(_q: str) -> list[EvidenceItem]:
        return list(raw_items)

    def guard(items: list[EvidenceItem]) -> list[EvidenceItem]:
        # AuthorizationGuard is applied at retrieval filter time; fail closed if empty.
        return items

    def rerank(_q: str, items: list[EvidenceItem]) -> list[EvidenceItem]:
        # ponytail: assumes guard never filters (true today — guard is a no-op
        # above); if guard starts filtering, rescope ranked_items to `items` here.
        allowed = {item.chunk_id for item in items}
        return [ranked_by_chunk_id[cid] for cid in ranked_by_chunk_id if cid in allowed]

    def generate(
        messages: Sequence[LLMMessage],
        max_tokens: int,
        temperature: float,
        seed: int,
    ) -> LLMCompletion:
        last_error: Exception | None = None
        for strategy, model_id, _kind in candidates:
            try:
                return strategy.complete(
                    messages,
                    model_id=model_id,
                    temperature=temperature,
                    seed=seed,
                    max_tokens=max_tokens,
                )
            except Exception as exc:  # noqa: BLE001 — try next configured provider
                last_error = exc
                continue
        assert last_error is not None
        raise last_error

    # E-labels here must match context_builder.build_context's own
    # sorted(evidence, key=lambda e: (-e.relevance, e.chunk_id)) exactly, since that
    # is what actually assigns E1..En inside run_doc_qa.
    ordered_for_labels = sorted(ranked_items, key=lambda e: (-e.relevance, e.chunk_id))
    citation_meta: dict[str, CitationMetadata] = {}
    for index, item in enumerate(ordered_for_labels):
        label = f"E{index + 1}"
        hit = hit_by_chunk_id.get(item.chunk_id)
        citation_meta[label] = CitationMetadata(
            evidence_id=label,
            title=str(hit.metadata.get("title") or hit.document_id) if hit else item.chunk_id,
            section_path=str(hit.metadata.get("section_path") or "") if hit else "",
            page=(int(hit.metadata.get("page") or 0) or None) if hit else None,
            table_ref=None,
            extraction_method=(
                str(hit.metadata.get("extraction_method") or "digital") if hit else "digital"
            ),
            relevance=item.relevance,
        )

    return run_doc_qa(
        question,
        retrieve=retrieve,
        guard=guard,
        rerank=rerank,
        generate=generate,
        gateway=gateway,
        citation_meta=citation_meta,
        history_summary=history_summary,
    )
