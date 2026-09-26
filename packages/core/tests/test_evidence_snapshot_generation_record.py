"""
File: test_evidence_snapshot_generation_record.py
Description: Immutable evidence snapshot and generation record (T3.15)
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

from seismobrain_adapters.evidence.inline import InlineEvidenceSnapshotStore
from seismobrain_core.evidence_snapshot_generation_record import (
    build_generation_record,
    prompt_context_hash,
    store_evidence_snapshots,
)
from seismobrain_core.grounded_prompt import (
    SYSTEM_PROMPT_VERSION,
    EvidencePromptBlock,
    build_grounded_prompt,
)


def test_prompt_context_hash_independently_recomputable() -> None:
    store = InlineEvidenceSnapshotStore(":memory:")
    prompt = build_grounded_prompt(
        question="torque?",
        evidence=[EvidencePromptBlock(evidence_id="E1", text="40 Nm")],
    )
    uris = store_evidence_snapshots(store, {"E1": "40 Nm"})
    record = build_generation_record(
        messages=prompt.messages,
        evidence_ids=["E1"],
        evidence_uris=uris,
        question="torque?",
        history_summary="",
        provider="stub",
        model="m",
        temperature=0.0,
        seed=42,
        max_output_tokens=100,
        system_prompt_version=SYSTEM_PROMPT_VERSION,
    )
    again = prompt_context_hash(
        messages=prompt.messages,
        evidence_ids=["E1"],
        template_version="grounded-v1",
    )
    assert again == record.prompt_context_hash
    assert store.get(uris["E1"]) == "40 Nm"
