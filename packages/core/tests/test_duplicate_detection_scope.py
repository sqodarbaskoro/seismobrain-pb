"""
File: test_duplicate_detection_scope.py
Description: FR-ACL-07 — file duplicate detection scoped to collection; no cross-scope signal
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

from seismobrain_core.duplicate_detection import CollectionDuplicateIndex


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_duplicate_detection_is_collection_scoped() -> None:
    index = CollectionDuplicateIndex()
    digest = _sha(b"same-bytes")
    assert index.find(tenant_id="t1", collection_id="c1", sha256=digest) is None
    index.register(
        tenant_id="t1",
        collection_id="c1",
        sha256=digest,
        document_id="doc-a",
    )
    assert index.find(tenant_id="t1", collection_id="c1", sha256=digest) == "doc-a"
    # Same bytes in another collection must not signal existence.
    assert index.find(tenant_id="t1", collection_id="c2", sha256=digest) is None
    # Same bytes in another tenant must not signal existence.
    assert index.find(tenant_id="t2", collection_id="c1", sha256=digest) is None
