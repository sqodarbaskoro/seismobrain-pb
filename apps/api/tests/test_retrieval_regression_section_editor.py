"""
File: test_retrieval_regression_section_editor.py
Description: Permanent CI regression guard for a high-overlap retrieval miss —
    Starter chat refused a question whose answer was ingested and indexed, because
    any-token-OR retrieval plus a no-op reranker buried the one correct chunk under
    weak single-token ("opsconsole") matches from unrelated content (FR-EVAL-01)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-18
Modified: 2026-09-19
Version: 0.2.0
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
from seismobrain_api.starter_ingest import register_starter_ingest
from seismobrain_core.roles import WorkspaceRole
from seismobrain_ingest.jobs import INGEST_JOB_NAME

_QUESTION = (
    "How does OpsConsole RT compute the batch sequence number in the Sequence Controller?"
)

_ANSWER_DOC = (
    "1.3 Section Editor\n\n"
    "The batch sequence number reported by OpsConsole RT is computed in the Sequence "
    "Controller from the anchor event, using the path distance from the start of line "
    "(DA) in Distance mode and elapsed time in Time mode."
)

# Weak single-token ("opsconsole") matches from unrelated content that previously
# outranked the real answer under any-token-OR scoring with a flat score.
_DISTRACTOR_DOC = "\n\n".join(
    f"OpsConsole node deployment note {i}: radio beacon height reference variance."
    for i in range(40)
)


def _ingest(container: AppContainer, *, document_id: str, filename: str, text: bytes) -> None:
    key = f"collections/col1/documents/{document_id}/{filename}"
    container.object_store.put(key, text)
    job_id = container.job_queue.enqueue(
        INGEST_JOB_NAME,
        {
            "document_id": document_id,
            "collection_id": "col1",
            "object_key": key,
            "filename": filename,
        },
    )
    container.job_queue.run_pending(timeout_seconds=5)
    assert container.job_queue.get_status(job_id) == "succeeded"


def test_section_editor_question_is_grounded_not_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    container = AppContainer(
        settings=Settings(),  # type: ignore[call-arg]
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
                                "The batch sequence number reported by OpsConsole RT "
                                "is computed in the Sequence Controller from the "
                                "anchor event, using the path distance from the start "
                                "of line (DA) in Distance mode and elapsed time in "
                                "Time mode. [E1]"
                            )
                        }
                    }
                ],
                "usage": {"prompt_tokens": 20, "completion_tokens": 40},
            }
        ),
    )
    register_starter_ingest(container)
    container.collection_access.map_collection("col1", "ws1")
    container.collection_access.set_workspace_role("u1", "ws1", WorkspaceRole.OWNER)
    container.collection_access.grant_write("u1", "col1")
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

    _ingest(
        container,
        document_id="ch03",
        filename="UserGuide_Chapter03_Data_Prep.md",
        text=_ANSWER_DOC.encode(),
    )
    _ingest(
        container,
        document_id="ch12",
        filename="UserGuide_Chapter12_Hardware.md",
        text=_DISTRACTOR_DOC.encode(),
    )

    result = run_conversation_doc_qa(
        container, question=_QUESTION, collection_ids=["col1"]
    )

    assert result.refusal is None, "must not refuse; the answer chunk is indexed"
    assert result.answer_text is not None
    assert "DA" in result.answer_text
    assert result.citations
    assert any("Chapter03" in c.title for c in result.citations)
