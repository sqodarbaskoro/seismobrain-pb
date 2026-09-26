"""
File: document_control.py
Description: Document-control field extraction (FR-PARSE-06)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-18
Version: 0.1.1
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DocumentControlFields:
    title: str
    document_number: str
    revision: str
    date: str
    author: str


_PATTERNS = {
    "document_number": re.compile(
        r"(?i)\b(?:doc(?:ument)?\s*(?:no|number|#)|document\s*id)\s*[:#]?\s*([A-Z0-9][\w\-./]+)"
    ),
    "revision": re.compile(r"(?i)\b(?:rev(?:ision)?|ver(?:sion)?)\s*[:#]?\s*([A-Z0-9.]+)"),
    "date": re.compile(
        r"(?i)\b(?:date|effective)\s*[:#]?\s*(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
    ),
    "author": re.compile(r"(?i)\b(?:author|prepared\s+by)\s*[:#]?\s*([A-Za-z][\w .'-]{1,60})"),
    "title": re.compile(r"(?i)\b(?:title)\s*[:#]?\s*(.+)"),
}


def extract_document_control(text: str, *, fallback_title: str = "") -> DocumentControlFields:
    fields: dict[str, str] = {
        "title": fallback_title,
        "document_number": "",
        "revision": "",
        "date": "",
        "author": "",
    }
    for key, pattern in _PATTERNS.items():
        match = pattern.search(text)
        if match:
            fields[key] = match.group(1).strip()
    if not fields["title"]:
        first = text.strip().splitlines()[0] if text.strip() else fallback_title
        fields["title"] = first[:120]
    return DocumentControlFields(**fields)


def field_accuracy(
    predicted: DocumentControlFields, gold: DocumentControlFields
) -> float:
    pairs = [
        (predicted.title, gold.title),
        (predicted.document_number, gold.document_number),
        (predicted.revision, gold.revision),
        (predicted.date, gold.date),
        (predicted.author, gold.author),
    ]
    correct = sum(1 for a, b in pairs if a.casefold() == b.casefold())
    return correct / len(pairs)
