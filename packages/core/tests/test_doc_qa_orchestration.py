"""
File: test_doc_qa_orchestration.py
Description: doc_qa end-to-end orchestration in core (T3.12)
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

from seismobrain_adapters.models.in_process import InProcessModelGateway
from seismobrain_core.citation_renderer import CitationMetadata
from seismobrain_core.context_builder import EvidenceItem
from seismobrain_core.doc_qa import run_doc_qa
from seismobrain_core.ports.llm_provider import LLMCompletion, LLMProviderKind


def test_doc_qa_happy_path_without_framework_imports() -> None:
    gateway = InProcessModelGateway()
    evidence = [
        EvidenceItem(
            chunk_id="c1",
            text="Torque for flange P2/94 is 40 Nm.",
            relevance=0.9,
        )
    ]

    def retrieve(_q: str) -> list[EvidenceItem]:
        return list(evidence)

    def guard(items: list[EvidenceItem]) -> list[EvidenceItem]:
        return items

    def rerank(_q: str, items: list[EvidenceItem]) -> list[EvidenceItem]:
        return items

    def generate(messages, max_tokens, temperature, seed):  # type: ignore[no-untyped-def]
        assert temperature == 0.0
        assert seed == 42
        assert max_tokens > 0
        assert any(m.role == "system" for m in messages)
        return LLMCompletion(
            text="Torque for flange P2/94 is 40 Nm [E1]",
            provider=LLMProviderKind.OPENAI_COMPATIBLE,
            model_id="stub",
        )

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
    assert result.answer_text is not None
    assert "[E1]" in result.answer_text
    assert result.citations
    assert result.support is not None
