"""
File: sample_load.py
Description: Index bundled sample corpus through ingest including EMBEDDED
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

import time
from dataclasses import dataclass, field
from pathlib import Path

from seismobrain_adapters.embedding_cache.sqlite import SqliteEmbeddingCache
from seismobrain_adapters.event_log.in_memory import InMemoryEventLog
from seismobrain_adapters.models.in_process import InProcessModelGateway
from seismobrain_core.chunking import SectionInput, chunk_document
from seismobrain_core.sparse_bm25_text import encode_bm25_text
from seismobrain_core.sparse_ident import encode_ident, has_identifiers
from seismobrain_core.sparse_term_registry import InMemorySparseTermRegistry
from seismobrain_ingest.embedded_stage import ChunkToEmbed, run_embedded_stage
from seismobrain_ingest.pipeline import INGEST_STAGES, IngestionPipeline, JobEventRecorder


def default_corpus_dir() -> Path:
    # packages/ingest/src/seismobrain_ingest/sample_load.py → repo root
    return Path(__file__).resolve().parents[4] / "samples" / "corpus"


@dataclass
class SampleLoadResult:
    files: int
    chunks: int
    embedded: int
    stages: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    overflow_splits: int = 0
    truncations: int = 0


def load_sample_corpus(
    *,
    corpus_dir: Path | None = None,
    work_dir: Path | None = None,
    smoke: bool = False,
) -> SampleLoadResult:
    """Index sample files end-to-end through the pipeline including EMBEDDED."""
    root = corpus_dir or default_corpus_dir()
    work = work_dir or (Path.cwd() / "data" / "sample_load")
    work.mkdir(parents=True, exist_ok=True)

    files = sorted(
        p for p in root.iterdir() if p.is_file() and p.suffix.lower() in {".md", ".txt"}
    )
    if smoke:
        files = files[:1]
    if not files:
        raise FileNotFoundError(f"no sample corpus files in {root}")

    gateway = InProcessModelGateway(embed_dim=32)
    cache = SqliteEmbeddingCache(work / "embed_cache.db")
    registry = InMemorySparseTermRegistry()
    event_log = InMemoryEventLog()
    recorder = JobEventRecorder()

    total_chunks = 0
    total_embedded = 0
    overflow = 0
    truncations = 0
    stages_seen: list[str] = []

    started = time.perf_counter()
    for index, path in enumerate(files):
        text = path.read_text(encoding="utf-8")
        chunk_result = chunk_document(
            [
                SectionInput(
                    section_id="s1",
                    heading_path=(path.stem,),
                    paragraphs=(text,),
                )
            ],
            document_title=path.stem,
        )
        overflow += chunk_result.overflow_splits
        truncations += chunk_result.truncations
        children = chunk_result.children
        total_chunks += len(children)

        chunks_to_embed = [
            ChunkToEmbed(
                chunk_id=c.chunk_id,
                document_id=f"doc-{index}",
                embedded_text=f"{c.contextual_header}\n{c.text}",
            )
            for c in children
        ]

        chunks_snapshot = list(chunks_to_embed)

        def stage_runner(
            stage: str,
            version_id: str,
            *,
            _chunks: list[ChunkToEmbed] = chunks_snapshot,
        ) -> dict[str, int]:
            _ = version_id
            if stage not in stages_seen:
                stages_seen.append(stage)
            if stage == "EMBEDDED":
                embedded = run_embedded_stage(
                    _chunks,
                    gateway=gateway,
                    cache=cache,
                    index_lookup={},
                    model_id="cpu-hash",
                    model_revision="rev1",
                )
                for chunk in _chunks:
                    encode_bm25_text(
                        chunk.embedded_text,
                        registry=registry,
                        encoder_version="id-bm25@1",
                    )
                    if has_identifiers(chunk.embedded_text):
                        encode_ident(
                            chunk.embedded_text,
                            registry=registry,
                            encoder_version="id-bm25@1",
                        )
                return {"items": len(embedded.items)}
            return {"items": 1}

        pipeline = IngestionPipeline(
            event_log=event_log,
            job_events=recorder,
            stage_runner=stage_runner,
        )
        result = pipeline.run(job_id=f"sample-{index}", version_id=f"ver-{index}")
        if result.status != "READY":
            raise RuntimeError(f"sample load failed at {result.stage}: {result.error}")
        total_embedded += len(chunks_to_embed)

    duration = time.perf_counter() - started
    return SampleLoadResult(
        files=len(files),
        chunks=total_chunks,
        embedded=total_embedded,
        stages=list(INGEST_STAGES) if "EMBEDDED" in stages_seen else stages_seen,
        duration_seconds=duration,
        overflow_splits=overflow,
        truncations=truncations,
    )


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Load SeismoBrain sample corpus")
    parser.add_argument("--smoke", action="store_true", help="Index one file only")
    parser.add_argument("--corpus", type=Path, default=None)
    args = parser.parse_args(argv)
    result = load_sample_corpus(corpus_dir=args.corpus, smoke=args.smoke)
    print(
        f"OK files={result.files} chunks={result.chunks} "
        f"embedded={result.embedded} duration_s={result.duration_seconds:.3f}"
    )
    if "EMBEDDED" not in result.stages and result.embedded == 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
