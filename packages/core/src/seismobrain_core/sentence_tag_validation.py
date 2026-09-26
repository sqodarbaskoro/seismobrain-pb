"""
File: sentence_tag_validation.py
Description: Segment sentences, validate E-tags, one repair attempt (FR-GEN-03)
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
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from seismobrain_core.evidence_tag_lint import lint_evidence_tags

_ETAG = re.compile(r"\[E(\d+)\]")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")

RepairFn = Callable[[str], str]


@dataclass(frozen=True, slots=True)
class ValidatedSentence:
    text: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ValidationResult:
    sentences: tuple[ValidatedSentence, ...]
    repaired: bool
    ok: bool


def segment_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_END.split(text.strip()) if s.strip()]


def strip_unknown_tags(sentence: str, *, allowed: Sequence[str]) -> str:
    allowed_set = set(allowed)

    def _replace(match: re.Match[str]) -> str:
        eid = f"E{match.group(1)}"
        return match.group(0) if eid in allowed_set else ""

    return _ETAG.sub(_replace, sentence).rstrip()


def extract_tags(sentence: str) -> tuple[str, ...]:
    return tuple(f"E{m.group(1)}" for m in _ETAG.finditer(sentence))


def validate_and_repair(
    text: str,
    *,
    allowed_evidence_ids: Sequence[str],
    repair: RepairFn | None = None,
) -> ValidationResult:
    """Validate tags against evidence set; one repair on format failure."""
    repaired = False
    candidate = text
    lint = lint_evidence_tags(candidate)
    if not lint.ok and repair is not None:
        candidate = repair(candidate)
        repaired = True
        lint = lint_evidence_tags(candidate)
    sentences: list[ValidatedSentence] = []
    for raw in segment_sentences(candidate):
        cleaned = strip_unknown_tags(raw, allowed=allowed_evidence_ids)
        tags = extract_tags(cleaned)
        sentences.append(ValidatedSentence(text=cleaned, evidence_ids=tags))
    ok = lint.ok and all(s.evidence_ids or s.text == "INSUFFICIENT_EVIDENCE" for s in sentences)
    if candidate.strip() == "INSUFFICIENT_EVIDENCE":
        ok = True
        sentences = [ValidatedSentence(text=candidate.strip(), evidence_ids=())]
    return ValidationResult(sentences=tuple(sentences), repaired=repaired, ok=ok)
