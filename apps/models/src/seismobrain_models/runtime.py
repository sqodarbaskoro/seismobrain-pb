"""
File: runtime.py
Description: CPU-only deterministic embed/sparse/rerank/verify implementations
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-17
Version: 0.2.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import hashlib
import math
import re

# Connective/functional words stripped before computing claim/evidence overlap so a
# paraphrased sentence ("...which indicates the subject is...") isn't penalized for
# wording that will never appear verbatim in terse source evidence.
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
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "as",
        "at",
        "by",
        "from",
        "with",
        "which",
        "who",
        "whom",
        "own",
        "only",
        "not",
        "can",
        "cannot",
        "does",
        "do",
        "did",
        "therefore",
        "further",
    }
)


def dense_embed(texts: list[str], *, dim: int = 32) -> list[list[float]]:
    out: list[list[float]] = []
    for text in texts:
        digest = hashlib.sha256(text.encode()).digest()
        vals = [((digest[i % len(digest)] / 255.0) * 2.0) - 1.0 for i in range(dim)]
        norm = math.sqrt(sum(v * v for v in vals)) or 1.0
        out.append([v / norm for v in vals])
    return out


def sparse_encode(texts: list[str]) -> list[dict[str, list[float] | list[int]]]:
    vectors: list[dict[str, list[float] | list[int]]] = []
    for text in texts:
        tokens = re.findall(r"[a-z0-9\-]+", text.lower())
        indices: list[int] = []
        values: list[float] = []
        for token in tokens:
            idx = int(hashlib.md5(token.encode()).hexdigest()[:6], 16) % 100_000
            indices.append(idx)
            values.append(1.0)
        vectors.append({"indices": indices, "values": values})
    return vectors


def rerank(query: str, documents: list[str]) -> list[int]:
    q = query.lower()
    scored = [
        (idx, doc.lower().count(q) + (1 if q in doc.lower() else 0))
        for idx, doc in enumerate(documents)
    ]
    scored.sort(key=lambda item: (-item[1], item[0]))
    return [idx for idx, _ in scored]


def verify_claim(claim: str, evidence: str) -> str:
    claim_l = claim.lower().strip()
    evidence_l = evidence.lower()
    if not claim_l:
        return "no_citation"
    if claim_l in evidence_l:
        return "supported"
    claim_tokens = {
        t for t in re.findall(r"[a-z0-9]+", claim_l) if t not in _STOPWORDS
    }
    evidence_tokens = set(re.findall(r"[a-z0-9]+", evidence_l))
    if not claim_tokens:
        return "unsupported"
    overlap = len(claim_tokens & evidence_tokens) / len(claim_tokens)
    if overlap >= 0.8:
        return "supported"
    if overlap >= 0.5:
        return "partial"
    return "unsupported"
