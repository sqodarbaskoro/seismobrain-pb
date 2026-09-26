"""
File: doc_qa.py
Description: End-to-end doc_qa orchestration in core (FR-RET-08, FR-GEN-05)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-18
Version: 0.2.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from seismobrain_core.answerability import EvidenceSnippet, heuristic_answerability
from seismobrain_core.citation_renderer import CitationMetadata, RenderedCitation, render_citations
from seismobrain_core.context_builder import EvidenceItem, build_context
from seismobrain_core.generation_params import generation_params_for_mode
from seismobrain_core.grounded_prompt import EvidencePromptBlock, build_grounded_prompt
from seismobrain_core.grounding_balanced import GroundingMode, GroundingResult, apply_grounding
from seismobrain_core.ports.llm_provider import LLMCompletion, LLMMessage
from seismobrain_core.ports.model_gateway import ModelGateway
from seismobrain_core.router import RouteClass, route_query
from seismobrain_core.sentence_tag_validation import validate_and_repair
from seismobrain_core.sentence_verifier import VerifiedSentence, verify_sentences
from seismobrain_core.support_label_stages import SupportLabelRecord, record_support_stages
from seismobrain_core.typed_refusals import Refusal, RefusalType, make_refusal

RetrieveFn = Callable[[str], list[EvidenceItem]]
GenerateFn = Callable[[Sequence[LLMMessage], int, float, int], LLMCompletion]
GuardFn = Callable[[list[EvidenceItem]], list[EvidenceItem]]
RerankFn = Callable[[str, list[EvidenceItem]], list[EvidenceItem]]

_logger = logging.getLogger(__name__)
_CONTENT_TOKEN = re.compile(r"[a-z0-9]+")
_REFUSAL_LOG_TOP_N = 5


def _token_overlap(query_tokens: frozenset[str], text: str) -> float:
    if not query_tokens:
        return 0.0
    tokens = set(_CONTENT_TOKEN.findall(text.lower()))
    if not tokens:
        return 0.0
    return len(query_tokens & tokens) / len(query_tokens)


def _log_refusal_diagnostics(
    question: str,
    ranked: Sequence[EvidenceItem],
    citation_meta: Mapping[str, CitationMetadata],
) -> None:
    """Titles + token-overlap only — never chunk/evidence text (no secrets/prompts
    in logs, per PRD). Diagnoses a weak-retrieval refusal from logs alone instead of
    requiring a corpus replay."""
    query_tokens = frozenset(_CONTENT_TOKEN.findall(question.lower()))
    ordered = sorted(ranked, key=lambda e: (-e.relevance, e.chunk_id))
    top = []
    for index, item in enumerate(ordered[:_REFUSAL_LOG_TOP_N]):
        meta = citation_meta.get(f"E{index + 1}")
        title = meta.title if meta is not None else item.chunk_id
        top.append(f"{title}={_token_overlap(query_tokens, item.text):.2f}")
    _logger.info("doc_qa refusal top_evidence=[%s]", ", ".join(top))


@dataclass(frozen=True, slots=True)
class DocQaResult:
    route: RouteClass
    grounding: GroundingResult | None
    citations: tuple[RenderedCitation, ...]
    support: SupportLabelRecord | None
    refusal: Refusal | None
    answer_text: str | None


def run_doc_qa(
    question: str,
    *,
    retrieve: RetrieveFn,
    guard: GuardFn,
    rerank: RerankFn,
    generate: GenerateFn,
    gateway: ModelGateway,
    citation_meta: Mapping[str, CitationMetadata],
    mode: GroundingMode = GroundingMode.BALANCED,
    max_context_tokens: int = 2000,
    history_summary: str = "",
) -> DocQaResult:
    """route → retrieve → guard → rerank → gate → context → generate → verify → render."""
    decision = route_query(question)
    if decision is not RouteClass.DOC_QA:
        return DocQaResult(
            route=decision,
            grounding=None,
            citations=(),
            support=None,
            refusal=make_refusal(RefusalType.OUT_OF_SCOPE),
            answer_text=None,
        )

    candidates = retrieve(question)
    authorized = guard(candidates)
    if not authorized:
        return DocQaResult(
            route=decision,
            grounding=None,
            citations=(),
            support=None,
            refusal=make_refusal(RefusalType.NO_EVIDENCE),
            answer_text=None,
        )
    ranked = rerank(question, authorized)
    gate = heuristic_answerability(
        question,
        [EvidenceSnippet(text=e.text, relevance=e.relevance) for e in ranked],
    )
    if not gate.answerable:
        _log_refusal_diagnostics(question, ranked, citation_meta)
        return DocQaResult(
            route=decision,
            grounding=None,
            citations=(),
            support=None,
            refusal=make_refusal(RefusalType.INSUFFICIENT_EVIDENCE),
            answer_text=None,
        )

    ctx = build_context(ranked, max_tokens=max_context_tokens)
    blocks = [
        EvidencePromptBlock(evidence_id=eid, text=item.text)
        for eid, item in ctx.blocks
    ]
    prompt = build_grounded_prompt(
        question=question, evidence=blocks, history_summary=history_summary
    )
    params = generation_params_for_mode(mode)
    try:
        completion = generate(
            prompt.messages,
            params.max_output_tokens,
            params.temperature,
            params.seed,
        )
    except Exception:
        return DocQaResult(
            route=decision,
            grounding=None,
            citations=(),
            support=None,
            refusal=make_refusal(RefusalType.PROVIDER_ERROR),
            answer_text=None,
        )

    if completion.text.strip() == "INSUFFICIENT_EVIDENCE":
        _log_refusal_diagnostics(question, ranked, citation_meta)
        return DocQaResult(
            route=decision,
            grounding=None,
            citations=(),
            support=None,
            refusal=make_refusal(RefusalType.INSUFFICIENT_EVIDENCE),
            answer_text=None,
        )

    allowed = [eid for eid, _ in ctx.blocks]
    validated = validate_and_repair(
        completion.text,
        allowed_evidence_ids=allowed,
        repair=lambda t: t if "[E" in t else (t.rstrip(". ") + " [E1]."),
    )
    evidence_map = {eid: item.text for eid, item in ctx.blocks}
    verified: list[VerifiedSentence] = verify_sentences(
        validated.sentences, evidence_text=evidence_map, gateway=gateway
    )
    grounding = apply_grounding(verified, mode=mode)
    if grounding.banner == "insufficient_evidence":
        _log_refusal_diagnostics(question, ranked, citation_meta)
        return DocQaResult(
            route=decision,
            grounding=grounding,
            citations=(),
            support=record_support_stages(verified, grounding.sentences),
            refusal=make_refusal(RefusalType.INSUFFICIENT_EVIDENCE),
            answer_text=None,
        )
    cited_ids: list[str] = []
    for sent in grounding.sentences:
        cited_ids.extend(sent.evidence_ids)
    citations = render_citations(cited_ids, metadata=citation_meta)
    support = record_support_stages(verified, grounding.sentences)
    answer = " ".join(s.text for s in grounding.sentences)
    return DocQaResult(
        route=decision,
        grounding=grounding,
        citations=tuple(citations),
        support=support,
        refusal=None,
        answer_text=answer,
    )
