"""
File: search_index.py
Description: In-memory search index with ACL + post-fusion guard (FR-RET-11)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-18
Version: 0.5.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import dataclasses
import json
import re
import sqlite3
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from seismobrain_core.sparse_bm25_text import Bm25Params, bm25_tf, tokenize_bm25_text

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_-]{1,}", re.IGNORECASE)
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "of",
        "to",
        "in",
        "on",
        "for",
        "is",
        "are",
        "was",
        "were",
        "be",
        "my",
        "our",
        "your",
        "what",
        "whats",
        "which",
        "who",
        "how",
        "when",
        "where",
        "why",
        "does",
        "do",
        "did",
        "can",
        "could",
        "would",
        "should",
        "about",
        "with",
        "from",
        "into",
        "this",
        "that",
        "these",
        "those",
        "me",
        "we",
        "you",
        "it",
        "its",
        "please",
        "tell",
        "show",
        "give",
        "list",
        "document",
        "documents",
        "doc",
        "docs",
        "file",
        "files",
    }
)


def _tokens(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(text.casefold()) if len(t) > 2 and t not in _STOPWORDS]


@dataclass(frozen=True, slots=True)
class IndexedHit:
    document_id: str
    version_id: str
    text: str
    collection_id: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class InMemorySearchIndex:
    """Chunks indexed for retrieval. Optionally write-through persists to SQLite via
    `db_path` — otherwise every chunk is lost on a Starter restart (T7.29), since
    ingest never writes them anywhere else."""

    hits: list[IndexedHit] = field(default_factory=list)
    db_path: Path | None = None

    def __post_init__(self) -> None:
        if self.db_path is None:
            return
        with self._connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS hits "
                "(rowid INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT NOT NULL)"
            )
            conn.commit()
            for (data,) in conn.execute("SELECT data FROM hits ORDER BY rowid"):
                self.hits.append(IndexedHit(**json.loads(data)))

    def _connect(self) -> sqlite3.Connection:
        assert self.db_path is not None
        return sqlite3.connect(self.db_path)

    def add(self, hit: IndexedHit) -> None:
        self.hits.append(hit)
        if self.db_path is None:
            return
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO hits (data) VALUES (?)",
                (json.dumps(dataclasses.asdict(hit)),),
            )
            conn.commit()

    def replace_document(self, document_id: str, hits: list[IndexedHit]) -> None:
        """Publish one document atomically; replaying a job never appends duplicates."""
        if any(hit.document_id != document_id for hit in hits):
            raise ValueError("Replacement chunks must belong to the document")
        if self.db_path is not None:
            with self._connect() as conn:
                conn.execute(
                    "DELETE FROM hits WHERE json_extract(data, '$.document_id') = ?", (document_id,)
                )
                conn.executemany(
                    "INSERT INTO hits (data) VALUES (?)",
                    [(json.dumps(dataclasses.asdict(hit)),) for hit in hits],
                )
                conn.commit()
        self.hits = [hit for hit in self.hits if hit.document_id != document_id] + hits

    def update_document_collection(self, document_id: str, collection_id: str) -> None:
        """Re-scope a moved document's chunks so retrieval ACL filtering follows the
        move (T7.30) — otherwise chunks stay attributed to the collection they were
        moved out of forever, since `add()` is the only other way hits change."""
        changed = False
        for i, hit in enumerate(self.hits):
            if hit.document_id == document_id and hit.collection_id != collection_id:
                self.hits[i] = dataclasses.replace(hit, collection_id=collection_id)
                changed = True
        if not changed or self.db_path is None:
            return
        # ponytail: full-table rewrite rather than a targeted UPDATE — hits aren't
        # tracked by rowid in memory. Fine at Starter's per-document chunk count and
        # move frequency; switch to keyed rows if that changes.
        with self._connect() as conn:
            conn.execute("DELETE FROM hits")
            conn.executemany(
                "INSERT INTO hits (data) VALUES (?)",
                [(json.dumps(dataclasses.asdict(h)),) for h in self.hits],
            )
            conn.commit()

    def query(
        self,
        *,
        text: str,
        collection_ids: list[str] | None = None,
        filters: dict[str, Any] | None = None,
        fallback_limit: int = 20,
    ) -> list[IndexedHit]:
        if self.db_path is not None:
            # Workers may publish through a separate process/instance.
            with self._connect() as conn:
                self.hits = [
                    IndexedHit(**json.loads(data))
                    for (data,) in conn.execute("SELECT data FROM hits ORDER BY rowid")
                ]
        tokens = _tokens(text)
        scoped = self._scoped(collection_ids=collection_ids, filters=filters)
        if not scoped:
            return []

        if tokens:
            query_terms = set(tokenize_bm25_text(text))
            params = Bm25Params()
            scored: list[tuple[float, IndexedHit]] = []
            for hit in scoped:
                hay = f"{hit.text} {hit.document_id} {hit.metadata.get('title', '')}"
                if not any(token in hay.casefold() for token in tokens):
                    continue
                doc_tokens = tokenize_bm25_text(hay)
                doc_len = len(doc_tokens)
                counts = Counter(doc_tokens)
                bm25_score = sum(
                    bm25_tf(tf=counts[term], doc_len=doc_len, params=params)
                    for term in query_terms
                    if term in counts
                )
                scored.append((bm25_score, hit))
            if scored:
                scored.sort(key=lambda pair: (pair[0], pair[1].score), reverse=True)
                return [hit for _score, hit in scored]

        # No discriminative keywords (or none matched): still return scoped docs so
        # Starter chat can answer "what's in my documents?" instead of empty-scope refusal.
        ranked = sorted(scoped, key=lambda h: h.score, reverse=True)
        return ranked[:fallback_limit]

    def _scoped(
        self,
        *,
        collection_ids: list[str] | None,
        filters: dict[str, Any] | None,
    ) -> list[IndexedHit]:
        results: list[IndexedHit] = []
        for hit in self.hits:
            if collection_ids and hit.collection_id not in collection_ids:
                continue
            if filters:
                skip = False
                for key, value in filters.items():
                    if hit.metadata.get(key) != value:
                        skip = True
                        break
                if skip:
                    continue
            results.append(hit)
        return results
