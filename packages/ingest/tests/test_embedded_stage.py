"""
File: test_embedded_stage.py
Description: FR-IDX-04 / FR-ING-02 — EMBEDDED stage via ModelGateway with cache
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

from pathlib import Path

import pytest

from seismobrain_adapters.embedding_cache.sqlite import SqliteEmbeddingCache
from seismobrain_adapters.event_log.in_memory import InMemoryEventLog
from seismobrain_adapters.models.in_process import InProcessModelGateway
from seismobrain_ingest.embedded_stage import (
    ChunkToEmbed,
    StageOrderError,
    require_embedded_before_index,
    run_embedded_stage,
)
from seismobrain_ingest.pipeline import INGEST_STAGES, IngestionPipeline, JobEventRecorder


def test_embedded_before_indexed_in_stage_order() -> None:
    assert INGEST_STAGES.index("EMBEDDED") < INGEST_STAGES.index("INDEXED")


def test_embedded_stage_batch_encodes_via_model_gateway(tmp_path: Path) -> None:
    gateway = InProcessModelGateway(embed_dim=8)
    cache = SqliteEmbeddingCache(tmp_path / "embed.db")
    chunks = [
        ChunkToEmbed(chunk_id="c1", document_id="d1", embedded_text="alpha pump"),
        ChunkToEmbed(chunk_id="c2", document_id="d1", embedded_text="beta valve"),
    ]
    result = run_embedded_stage(
        chunks,
        gateway=gateway,
        cache=cache,
        index_lookup={},
        model_id="cpu-hash",
        model_revision="rev1",
    )
    assert len(result.items) == 2
    assert all(len(item.vector) == 8 for item in result.items)
    assert all(item.source == "encode" for item in result.items)
    assert result.encode_calls == 1
    assert result.encoded_texts == 2


def test_embedded_stage_reuses_cache_before_encode(tmp_path: Path) -> None:
    gateway = InProcessModelGateway(embed_dim=8)
    cache = SqliteEmbeddingCache(tmp_path / "embed.db")
    chunk = ChunkToEmbed(chunk_id="c1", document_id="d1", embedded_text="same text")
    first = run_embedded_stage(
        [chunk],
        gateway=gateway,
        cache=cache,
        index_lookup={},
        model_id="cpu-hash",
        model_revision="rev1",
    )
    assert first.items[0].source == "encode"
    second = run_embedded_stage(
        [ChunkToEmbed(chunk_id="c2", document_id="d2", embedded_text="same text")],
        gateway=gateway,
        cache=cache,
        index_lookup={},
        model_id="cpu-hash",
        model_revision="rev1",
    )
    assert second.items[0].source == "cache"
    assert second.encode_calls == 0
    assert second.items[0].vector == first.items[0].vector


def test_embedded_stage_reuses_index_before_cache(tmp_path: Path) -> None:
    gateway = InProcessModelGateway(embed_dim=4)
    cache = SqliteEmbeddingCache(tmp_path / "embed.db")
    from seismobrain_core.embedding_reuse import compute_text_hash

    text = "indexed already"
    th = compute_text_hash(text)
    index_vec = [0.1, 0.2, 0.3, 0.4]
    result = run_embedded_stage(
        [ChunkToEmbed(chunk_id="c1", document_id="d1", embedded_text=text)],
        gateway=gateway,
        cache=cache,
        index_lookup={(th, "cpu-hash", "rev1"): index_vec},
        model_id="cpu-hash",
        model_revision="rev1",
    )
    assert result.items[0].source == "index"
    assert result.items[0].vector == index_vec
    assert result.encode_calls == 0


def test_pipeline_cannot_skip_embedded_before_indexed(tmp_path: Path) -> None:
    event_log = InMemoryEventLog()
    recorder = JobEventRecorder()
    seen: list[str] = []

    def runner(stage: str, version_id: str) -> dict[str, int]:
        _ = version_id
        if stage == "INDEXED" and "EMBEDDED" not in seen:
            raise StageOrderError("EMBEDDED must complete before INDEXED")
        seen.append(stage)
        if stage == "EMBEDDED":
            run_embedded_stage(
                [ChunkToEmbed(chunk_id="c1", document_id="d1", embedded_text="x")],
                gateway=InProcessModelGateway(embed_dim=4),
                cache=SqliteEmbeddingCache(tmp_path / "e.db"),
                index_lookup={},
                model_id="cpu-hash",
                model_revision="rev1",
            )
        return {"items": 1}

    pipeline = IngestionPipeline(
        event_log=event_log, job_events=recorder, stage_runner=runner
    )
    result = pipeline.run(job_id="j1", version_id="v1")
    assert result.status == "READY"
    assert seen.index("EMBEDDED") < seen.index("INDEXED")


def test_index_without_embedded_raises() -> None:
    with pytest.raises(StageOrderError):
        require_embedded_before_index(embedded_completed=False)
