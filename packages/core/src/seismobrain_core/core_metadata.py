"""
File: core_metadata.py
Description: Core document metadata fields and filter helpers (FR-META-01)
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

from dataclasses import dataclass
from typing import Any

# source_path is internal-only: API may filter on it for admins but must not emit it
# to end-user browse responses unless explicitly elevated (handled by redaction).
CORE_METADATA_FIELDS = (
    "title",
    "doc_type",
    "revision",
    "effective_date",
    "author",
    "language",
    "tags",
    "source_path",
)

PUBLIC_METADATA_FIELDS = tuple(f for f in CORE_METADATA_FIELDS if f != "source_path")


@dataclass(frozen=True, slots=True)
class CoreMetadata:
    title: str
    doc_type: str = ""
    revision: str = ""
    effective_date: str = ""
    author: str = ""
    language: str = ""
    tags: tuple[str, ...] = ()
    source_path: str = ""

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "doc_type": self.doc_type,
            "revision": self.revision,
            "effective_date": self.effective_date,
            "author": self.author,
            "language": self.language,
            "tags": list(self.tags),
        }

    def matches(
        self,
        *,
        title: str | None = None,
        doc_type: str | None = None,
        revision: str | None = None,
        effective_date: str | None = None,
        author: str | None = None,
        language: str | None = None,
        tag: str | None = None,
        source_path: str | None = None,
    ) -> bool:
        if title and title.lower() not in self.title.lower():
            return False
        if doc_type and self.doc_type != doc_type:
            return False
        if revision and self.revision != revision:
            return False
        if effective_date and self.effective_date != effective_date:
            return False
        if author and self.author != author:
            return False
        if language and self.language != language:
            return False
        if tag and tag not in self.tags:
            return False
        if source_path and self.source_path != source_path:
            return False
        return True
