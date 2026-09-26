"""
File: test_chat_doc_qa_rerank.py
Description: Rerank must change which chunk lands as E1, and citation_meta must stay
    in sync with that reranked order (FR-RET-03)
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

from pathlib import Path

import pytest

from seismobrain_adapters.authz.deny import DenyAllAuthorizationGuard
from seismobrain_adapters.event_log.in_memory import InMemoryEventLog
from seismobrain_adapters.llm.transport import RecordingTransport
from seismobrain_adapters.metadata.sqlite import SqliteMetadataStore
from seismobrain_adapters.object_store.filesystem import FilesystemObjectStore
from seismobrain_adapters.queue.in_process import InProcessJobQueue
from seismobrain_adapters.rate_limit.in_memory import InMemoryRateLimiter
from seismobrain_api.auth.users import InMemoryUserStore
from seismobrain_api.chat_doc_qa import run_conversation_doc_qa
from seismobrain_api.config import Settings
from seismobrain_api.container import AppContainer
from seismobrain_api.search_index import IndexedHit

_QUESTION = "torque procedure for flange bolts"

# High BM25 term frequency (many repeats of "torque"/"procedure"/"flange"/"bolts")
# but never the literal query phrase — wins on raw BM25 alone.
_BM25_WINNER_TEXT = (
    "Torque torque torque procedure bolts flange procedure notes bolts torque."
)
# Lower term frequency (each word once) but contains the exact query phrase as a
# substring — the placeholder reranker (seismobrain_models.runtime.rerank) scores
# substring/full-phrase matches, so it should promote this chunk to E1.
_RERANK_WINNER_TEXT = "See the torque procedure for flange bolts in section 4."


def _build_container(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AppContainer:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    settings = Settings()  # type: ignore[call-arg]
    container = AppContainer(
        settings=settings,
        metadata_store=SqliteMetadataStore(tmp_path / "meta.db"),
        job_queue=InProcessJobQueue(tmp_path / "jobs"),
        object_store=FilesystemObjectStore(tmp_path / "objects"),
        event_log=InMemoryEventLog(),
        rate_limiter=InMemoryRateLimiter(),
        authorization_guard=DenyAllAuthorizationGuard(),
        user_store=InMemoryUserStore(),
        llm_transport=RecordingTransport(
            response={
                "choices": [
                    {
                        "message": {
                            "content": (
                                "See the torque procedure for flange bolts in "
                                "section 4. [E1]"
                            )
                        }
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 8},
            }
        ),
    )
    container.admin_catalog.create_provider(
        kind="openai_compatible",
        name="test-llm",
        models=["test-model"],
        api_key="sk-test",
        master_key=container.settings.master_key,
        actor="test",
        base_url="https://openrouter.ai/api/v1",
        locality="external",
    )
    container.search_index.add(
        IndexedHit(
            document_id="bm25-winner",
            version_id="bm25-winner:v1",
            text=_BM25_WINNER_TEXT,
            collection_id="ops",
            score=1.0,
            metadata={"title": "Ch12_Hardware", "chunk_id": "bm25-winner"},
        )
    )
    container.search_index.add(
        IndexedHit(
            document_id="rerank-winner",
            version_id="rerank-winner:v1",
            text=_RERANK_WINNER_TEXT,
            collection_id="ops",
            score=1.0,
            metadata={"title": "Ch03_Data_Prep", "chunk_id": "rerank-winner"},
        )
    )
    return container


def test_bm25_alone_prefers_the_higher_term_frequency_chunk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sanity check on the fixture: without rerank, BM25 term frequency alone would
    rank the wrong chunk first (proves rerank is the thing doing real work below)."""
    container = _build_container(tmp_path, monkeypatch)
    hits = container.search_index.query(text=_QUESTION, collection_ids=["ops"])
    assert hits[0].document_id == "bm25-winner"


def test_rerank_promotes_the_phrase_match_to_e1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    container = _build_container(tmp_path, monkeypatch)
    result = run_conversation_doc_qa(
        container, question=_QUESTION, collection_ids=["ops"]
    )
    assert result.refusal is None
    assert result.citations
    assert result.citations[0].evidence_id == "E1"
    assert result.citations[0].title == "Ch03_Data_Prep"
