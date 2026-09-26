"""
File: test_doc_qa_refusal_diagnostics.py
Description: INSUFFICIENT_EVIDENCE refusals log top-evidence titles + overlap so a
    weak-retrieval refusal is diagnosable from logs alone (no chunk text) (NFR-MAINT-01)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-18
Modified: 2026-09-19
Version: 0.1.1
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import logging

import pytest

from seismobrain_adapters.models.in_process import InProcessModelGateway
from seismobrain_core.citation_renderer import CitationMetadata
from seismobrain_core.context_builder import EvidenceItem
from seismobrain_core.doc_qa import run_doc_qa
from seismobrain_core.ports.llm_provider import LLMCompletion, LLMProviderKind

_UNRELATED_EVIDENCE_TEXT = (
    "Radio beacon height reference variance for node deployment."
)


def _generate(messages, max_tokens, temperature, seed):  # type: ignore[no-untyped-def]
    return LLMCompletion(
        text="INSUFFICIENT_EVIDENCE",
        provider=LLMProviderKind.OPENAI_COMPATIBLE,
        model_id="stub",
    )


def test_refusal_logs_top_evidence_titles_and_overlap_not_text(
    caplog: pytest.LogCaptureFixture,
) -> None:
    gateway = InProcessModelGateway()
    evidence = [
        EvidenceItem(chunk_id="c1", text=_UNRELATED_EVIDENCE_TEXT, relevance=1.0)
    ]

    def retrieve(_q: str) -> list[EvidenceItem]:
        return list(evidence)

    def guard(items: list[EvidenceItem]) -> list[EvidenceItem]:
        return items

    def rerank(_q: str, items: list[EvidenceItem]) -> list[EvidenceItem]:
        return items

    with caplog.at_level(logging.INFO, logger="seismobrain_core.doc_qa"):
        result = run_doc_qa(
            "What is the torque for flange P2/94?",
            retrieve=retrieve,
            guard=guard,
            rerank=rerank,
            generate=_generate,
            gateway=gateway,
            citation_meta={
                "E1": CitationMetadata(
                    evidence_id="E1",
                    title="Ch12_Hardware",
                    section_path="2.1",
                    page=5,
                    table_ref=None,
                    extraction_method="digital",
                )
            },
        )

    assert result.refusal is not None
    messages = [r.getMessage() for r in caplog.records]
    assert any("Ch12_Hardware" in m for m in messages)
    assert not any(_UNRELATED_EVIDENCE_TEXT in m for m in messages)


def test_grounded_answer_does_not_log_refusal_diagnostics(
    caplog: pytest.LogCaptureFixture,
) -> None:
    gateway = InProcessModelGateway()
    evidence = [
        EvidenceItem(
            chunk_id="c1", text="Torque for flange P2/94 is 40 Nm.", relevance=0.9
        )
    ]

    def retrieve(_q: str) -> list[EvidenceItem]:
        return list(evidence)

    def guard(items: list[EvidenceItem]) -> list[EvidenceItem]:
        return items

    def rerank(_q: str, items: list[EvidenceItem]) -> list[EvidenceItem]:
        return items

    def generate(messages, max_tokens, temperature, seed):  # type: ignore[no-untyped-def]
        return LLMCompletion(
            text="Torque for flange P2/94 is 40 Nm [E1]",
            provider=LLMProviderKind.OPENAI_COMPATIBLE,
            model_id="stub",
        )

    with caplog.at_level(logging.INFO, logger="seismobrain_core.doc_qa"):
        result = run_doc_qa(
            "What is the torque for flange P2/94?",
            retrieve=retrieve,
            guard=guard,
            rerank=rerank,
            generate=generate,
            gateway=gateway,
            citation_meta={
                "E1": CitationMetadata(
                    evidence_id="E1",
                    title="Ops",
                    section_path="4.2",
                    page=12,
                    table_ref=None,
                    extraction_method="digital",
                )
            },
        )

    assert result.refusal is None
    assert not caplog.records
