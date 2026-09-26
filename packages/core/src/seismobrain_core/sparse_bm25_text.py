"""
File: sparse_bm25_text.py
Description: bm25_text sparse arm tokenization and BM25 TF (§8.4.1–8.4.2)
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

import re
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

DEFAULT_BM25_K1 = 1.2
DEFAULT_BM25_B = 0.75
DEFAULT_BM25_AVG_LEN = 100.0
DEFAULT_MAX_NUMERIC_LEN = 8
ARM_BM25_TEXT = "bm25_text"

_WORD_PART = re.compile(r"[a-z0-9]+", re.IGNORECASE)

_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "if",
        "then",
        "else",
        "when",
        "at",
        "by",
        "for",
        "with",
        "about",
        "against",
        "between",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "to",
        "from",
        "up",
        "down",
        "in",
        "out",
        "on",
        "off",
        "over",
        "under",
        "again",
        "further",
        "once",
        "here",
        "there",
        "all",
        "any",
        "both",
        "each",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "nor",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "can",
        "will",
        "just",
        "don",
        "should",
        "now",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "having",
        "do",
        "does",
        "did",
        "doing",
        "of",
        "as",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "they",
        "them",
        "their",
        "we",
        "you",
        "he",
        "she",
        "his",
        "her",
        "our",
        "my",
    }
)


class _Registry(Protocol):
    def get_or_assign(self, encoder_version: str, arm: str, token: str) -> int: ...


@dataclass(frozen=True, slots=True)
class Bm25Params:
    """Pinned BM25 parameters for one index version (PRD §8.4.2)."""

    k1: float = DEFAULT_BM25_K1
    b: float = DEFAULT_BM25_B
    avg_len: float = DEFAULT_BM25_AVG_LEN


@dataclass(frozen=True, slots=True)
class SparseVector:
    indices: tuple[int, ...]
    values: tuple[float, ...]


def _is_consonant(word: str, i: int) -> bool:
    ch = word[i]
    if ch in "aeiou":
        return False
    if ch == "y":
        return i == 0 or not _is_consonant(word, i - 1)
    return True


def _measure(stem: str) -> int:
    """Porter measure m of a stem."""
    n = 0
    i = 0
    length = len(stem)
    while i < length and _is_consonant(stem, i):
        i += 1
    while i < length:
        while i < length and not _is_consonant(stem, i):
            i += 1
        n += 1
        while i < length and _is_consonant(stem, i):
            i += 1
    return n


def _has_vowel(stem: str) -> bool:
    return any(not _is_consonant(stem, i) for i in range(len(stem)))


def _ends_double_consonant(stem: str) -> bool:
    return len(stem) >= 2 and stem[-1] == stem[-2] and _is_consonant(stem, len(stem) - 1)


def _ends_cvc(stem: str) -> bool:
    if len(stem) < 3:
        return False
    return (
        _is_consonant(stem, len(stem) - 1)
        and not _is_consonant(stem, len(stem) - 2)
        and _is_consonant(stem, len(stem) - 3)
        and stem[-1] not in "wxy"
    )


def porter_stem(word: str) -> str:
    """Compact Porter stemmer (English) for bm25_text tokens."""
    if len(word) <= 2:
        return word
    w = word

    # Step 1a
    if w.endswith("sses"):
        w = w[:-2]
    elif w.endswith("ies"):
        w = w[:-2]
    elif w.endswith("ss"):
        pass
    elif w.endswith("s") and not w.endswith("us") and not w.endswith("ss"):
        w = w[:-1]

    # Step 1b
    step1b_extra = False
    if w.endswith("eed"):
        stem = w[:-3]
        if _measure(stem) > 0:
            w = stem + "ee"
    elif w.endswith("ed"):
        stem = w[:-2]
        if _has_vowel(stem):
            w = stem
            step1b_extra = True
    elif w.endswith("ing"):
        stem = w[:-3]
        if _has_vowel(stem):
            w = stem
            step1b_extra = True

    if step1b_extra:
        if w.endswith(("at", "bl", "iz")):
            w += "e"
        elif _ends_double_consonant(w) and w[-1] not in "lsz":
            w = w[:-1]
        elif _measure(w) == 1 and _ends_cvc(w):
            w += "e"

    # Step 1c
    if w.endswith("y") and _has_vowel(w[:-1]):
        w = w[:-1] + "i"

    # Step 2
    step2 = {
        "ational": "ate",
        "tional": "tion",
        "enci": "ence",
        "anci": "ance",
        "izer": "ize",
        "abli": "able",
        "alli": "al",
        "entli": "ent",
        "eli": "e",
        "ousli": "ous",
        "ization": "ize",
        "ation": "ate",
        "ator": "ate",
        "alism": "al",
        "iveness": "ive",
        "fulness": "ful",
        "ousness": "ous",
        "aliti": "al",
        "iviti": "ive",
        "biliti": "ble",
    }
    for suffix, repl in step2.items():
        if w.endswith(suffix):
            stem = w[: -len(suffix)]
            if _measure(stem) > 0:
                w = stem + repl
            break

    # Step 3
    step3 = {
        "icate": "ic",
        "ative": "",
        "alize": "al",
        "iciti": "ic",
        "ical": "ic",
        "ful": "",
        "ness": "",
    }
    for suffix, repl in step3.items():
        if w.endswith(suffix):
            stem = w[: -len(suffix)]
            if _measure(stem) > 0:
                w = stem + repl
            break

    # Step 4
    step4 = (
        "al",
        "ance",
        "ence",
        "er",
        "ic",
        "able",
        "ible",
        "ant",
        "ement",
        "ment",
        "ent",
        "ion",
        "ou",
        "ism",
        "ate",
        "iti",
        "ous",
        "ive",
        "ize",
    )
    for suffix in step4:
        if w.endswith(suffix):
            stem = w[: -len(suffix)]
            if suffix == "ion":
                if stem and stem[-1] in "st" and _measure(stem) > 1:
                    w = stem
            elif _measure(stem) > 1:
                w = stem
            break

    # Step 5a
    if w.endswith("e"):
        stem = w[:-1]
        m = _measure(stem)
        if m > 1 or (m == 1 and not _ends_cvc(stem)):
            w = stem

    # Step 5b
    if _measure(w) > 1 and _ends_double_consonant(w) and w.endswith("l"):
        w = w[:-1]

    return w


def tokenize_bm25_text(
    text: str,
    *,
    max_numeric_len: int = DEFAULT_MAX_NUMERIC_LEN,
) -> list[str]:
    """Lowercase, split identifiers into word parts, drop stopwords, stem."""
    lowered = text.lower()
    parts = _WORD_PART.findall(lowered)
    out: list[str] = []
    for part in parts:
        if part in _STOPWORDS:
            continue
        if part.isdigit() and len(part) > max_numeric_len:
            continue
        stemmed = porter_stem(part) if not part.isdigit() else part
        if stemmed and stemmed not in _STOPWORDS:
            out.append(stemmed)
    return out


def bm25_tf(*, tf: int, doc_len: int, params: Bm25Params) -> float:
    """BM25 term frequency component with pinned k1/b/avg_len (IDF from Qdrant)."""
    if tf <= 0 or doc_len <= 0 or params.avg_len <= 0:
        return 0.0
    denom = tf + params.k1 * (1.0 - params.b + params.b * (doc_len / params.avg_len))
    return (tf * (params.k1 + 1.0)) / denom


def encode_bm25_text(
    text: str,
    *,
    registry: _Registry,
    encoder_version: str,
    params: Bm25Params | None = None,
    max_numeric_len: int = DEFAULT_MAX_NUMERIC_LEN,
) -> SparseVector:
    """Encode text into a sparse vector via term registry + BM25 TF weights."""
    pinned = params if params is not None else Bm25Params()
    tokens = tokenize_bm25_text(text, max_numeric_len=max_numeric_len)
    doc_len = len(tokens)
    counts: Mapping[str, int] = Counter(tokens)
    indices: list[int] = []
    values: list[float] = []
    for token, tf in sorted(counts.items()):
        idx = registry.get_or_assign(encoder_version, ARM_BM25_TEXT, token)
        weight = bm25_tf(tf=tf, doc_len=doc_len, params=pinned)
        indices.append(idx)
        values.append(weight)
    return SparseVector(indices=tuple(indices), values=tuple(values))
