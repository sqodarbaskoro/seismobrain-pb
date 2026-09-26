"""
File: test_document_versioning.py
Description: Versioning by logical key with activation (T5.19)
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

from seismobrain_ingest.document_versioning import DocumentVersionIndex
from seismobrain_ingest.version_activation import (
    ActivationStore,
    VectorPointState,
    activate_version,
)


def test_logical_key_latest_default_and_activation_holds() -> None:
    index = DocumentVersionIndex()
    doc_id = index.register(logical_key="OPS-204", version_id="v1")
    index.register(logical_key="OPS-204", version_id="v2")
    assert index.latest("OPS-204") == "v2"
    assert index.document_id("OPS-204") == doc_id
    assert index.history("OPS-204") == ["v1", "v2"]

    store = ActivationStore()
    store.set_current(doc_id, "v1")
    store.points[doc_id] = [
        VectorPointState(point_id="p1", version_id="v1", is_latest=True, verified=True)
    ]
    activate_version(
        store,
        document_id=doc_id,
        old_version_id="v1",
        new_version_id="v2",
        new_point_ids=["p2"],
    )
    assert store.current_version_id[doc_id] == "v2"
    assert store.query_visible_versions(doc_id) == ["v2"]
