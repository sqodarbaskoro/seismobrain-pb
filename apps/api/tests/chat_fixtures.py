"""
File: chat_fixtures.py
Description: Shared fixtures to seed retrieval + LLM for conversation stream tests
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-17
Modified: 2026-09-17
Version: 0.1.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from seismobrain_adapters.llm.transport import RecordingTransport
from seismobrain_api.container import AppContainer
from seismobrain_api.search_index import IndexedHit


def seed_grounded_chat(container: AppContainer) -> None:
    """Configure a recorded LLM provider and one searchable evidence chunk."""
    container.llm_transport = RecordingTransport(
        response={
            "choices": [
                {
                    "message": {
                        "content": "Torque for flange P2/94 is 40 Nm [E1]",
                    }
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 8},
        }
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
            document_id="doc-1",
            version_id="doc-1:v1",
            text="Torque for flange P2/94 is 40 Nm.",
            collection_id="ops",
            score=1.0,
            metadata={
                "chunk_id": "c1",
                "title": "Ops Manual",
                "section_path": "4.2",
                "page": 12,
                "extraction_method": "digital",
            },
        )
    )
