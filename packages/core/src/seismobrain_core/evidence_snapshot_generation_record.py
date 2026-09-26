"""
File: evidence_snapshot_generation_record.py
Description: Immutable evidence snapshot + generation record hashing (FR-CHAT-08)
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

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from seismobrain_core.ports.evidence_snapshot_store import EvidenceSnapshotStore
from seismobrain_core.ports.llm_provider import LLMMessage


@dataclass(frozen=True, slots=True)
class GenerationRecord:
    prompt_context_hash: str
    prompt_template_version: str
    system_prompt_version: str
    question_snapshot: str
    history_summary_snapshot: str
    provider: str
    model: str
    temperature: float
    seed: int
    max_output_tokens: int
    evidence_uris: Mapping[str, str]
    prompt_blob_uri: str | None = None


def prompt_context_hash(
    *,
    messages: Sequence[LLMMessage],
    evidence_ids: Sequence[str],
    template_version: str,
) -> str:
    payload = {
        "messages": [{"role": m.role, "content": m.content} for m in messages],
        "evidence_ids": list(evidence_ids),
        "template_version": template_version,
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


def store_evidence_snapshots(
    store: EvidenceSnapshotStore,
    evidence: Mapping[str, str],
) -> dict[str, str]:
    return {eid: store.put(text) for eid, text in evidence.items()}


def build_generation_record(
    *,
    messages: Sequence[LLMMessage],
    evidence_ids: Sequence[str],
    evidence_uris: Mapping[str, str],
    question: str,
    history_summary: str,
    provider: str,
    model: str,
    temperature: float,
    seed: int,
    max_output_tokens: int,
    system_prompt_version: str,
    prompt_template_version: str = "grounded-v1",
    prompt_blob_uri: str | None = None,
) -> GenerationRecord:
    return GenerationRecord(
        prompt_context_hash=prompt_context_hash(
            messages=messages,
            evidence_ids=evidence_ids,
            template_version=prompt_template_version,
        ),
        prompt_template_version=prompt_template_version,
        system_prompt_version=system_prompt_version,
        question_snapshot=question,
        history_summary_snapshot=history_summary,
        provider=provider,
        model=model,
        temperature=temperature,
        seed=seed,
        max_output_tokens=max_output_tokens,
        evidence_uris=dict(evidence_uris),
        prompt_blob_uri=prompt_blob_uri,
    )


def generation_record_as_dict(record: GenerationRecord) -> dict[str, Any]:
    return {
        "prompt_context_hash": record.prompt_context_hash,
        "prompt_template_version": record.prompt_template_version,
        "system_prompt_version": record.system_prompt_version,
        "question_snapshot": record.question_snapshot,
        "history_summary_snapshot": record.history_summary_snapshot,
        "provider": record.provider,
        "model": record.model,
        "temperature": record.temperature,
        "seed": record.seed,
        "max_output_tokens": record.max_output_tokens,
        "evidence_uris": dict(record.evidence_uris),
        "prompt_blob_uri": record.prompt_blob_uri,
    }
