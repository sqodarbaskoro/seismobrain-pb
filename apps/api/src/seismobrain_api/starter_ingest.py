"""
File: starter_ingest.py
Description: Starter-tier ingest handler — parse documents, index chunks for chat retrieval
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-17
Modified: 2026-09-18
Version: 0.6.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING

from seismobrain_api.document_text import extract_document_sections
from seismobrain_api.search_index import IndexedHit
from seismobrain_core.chunking import SectionInput, chunk_document
from seismobrain_core.job_execution import ingestion_publication, ingestion_stage
from seismobrain_ingest.jobs import INGEST_JOB_NAME
from seismobrain_ingest.page_mapping import map_chunk_to_page
from seismobrain_ingest.parsers_p0 import extract_pdf_page_texts

if TYPE_CHECKING:
    from seismobrain_api.container import AppContainer
    from seismobrain_core.ports import JobQueue


def make_ingest_handler(container: AppContainer) -> Callable[[Mapping[str, object]], None]:
    def handle(payload: Mapping[str, object]) -> None:
        document_id = str(payload["document_id"])
        collection_id = str(payload["collection_id"])
        object_key = str(payload.get("object_key", ""))
        filename = str(payload.get("filename", "document.txt"))
        if not object_key:
            raise ValueError("object_key required")
        with ingestion_stage("PARSED") as counts:
            raw = container.object_store.get(object_key)
            title = filename.rsplit(".", 1)[0] or filename
            pages = extract_pdf_page_texts(raw) if filename.lower().endswith(".pdf") else []
            sections = extract_document_sections(filename, raw)
            counts["pages"] = len(pages)
            counts["sections"] = len(sections)
        with ingestion_stage("CHUNKED") as counts:
            chunk_result = chunk_document(
                [
                    SectionInput(
                        section_id=f"s{index + 1}",
                        heading_path=heading_path or (title,),
                        paragraphs=tuple(paragraphs),
                    )
                    for index, (heading_path, paragraphs) in enumerate(sections)
                ],
                document_title=title,
            )
            counts["chunks"] = len(chunk_result.children)
            hits: list[IndexedHit] = []
            for index, child in enumerate(chunk_result.children):
                evidence_label = f"E{index + 1}"
                # chunk_document() numbers chunks fresh per call (one call per document
                # here), so a bare chunk_id collides across documents in the shared
                # search index; namespace it with document_id to keep it globally unique.
                chunk_id = f"{document_id}:{child.chunk_id}"
                chunk_page = map_chunk_to_page(
                    chunk_id=chunk_id, chunk_text=child.text, pages=pages
                )
                hits.append(
                    IndexedHit(
                        document_id=document_id,
                        version_id=f"{document_id}:v1",
                        text=f"{child.contextual_header}\n{child.text}".strip(),
                        collection_id=collection_id,
                        score=1.0,
                        metadata={
                            "chunk_id": chunk_id,
                            "title": title,
                            "section_path": " / ".join(child.heading_path)
                            if child.heading_path
                            else "1",
                            "page": chunk_page.page,
                            "extraction_method": "digital",
                            "evidence_label": evidence_label,
                        },
                    )
                )

        with ingestion_stage("INDEXED") as counts:
            with ingestion_publication():
                container.collection_access.add_document(
                    document_id=document_id,
                    collection_id=collection_id,
                    title=title,
                    doc_type=filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt",
                    source_path=filename,
                    object_key=object_key,
                )
                container.search_index.replace_document(document_id, hits)
            counts["chunks"] = len(hits)

    return handle


def register_starter_ingest(container: AppContainer) -> None:
    container.job_queue.register(INGEST_JOB_NAME, make_ingest_handler(container))


def start_ingest_worker(queue: JobQueue, *, poll_seconds: float = 0.25) -> threading.Thread:
    def loop() -> None:
        while True:
            try:
                queue.run_pending(timeout_seconds=1.0)
            except Exception:
                logging.getLogger(__name__).error("Ingestion worker polling failed")
            time.sleep(poll_seconds)

    thread = threading.Thread(target=loop, name="starter-ingest", daemon=True)
    thread.start()
    return thread
