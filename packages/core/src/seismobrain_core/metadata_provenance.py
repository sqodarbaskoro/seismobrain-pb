"""
File: metadata_provenance.py
Description: Metadata value source and confidence (FR-META-03)
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
from enum import StrEnum


class MetadataSource(StrEnum):
    PATH_TEMPLATE = "path_template"
    DOCUMENT_CONTROL = "document_control"
    USER = "user"
    INFERRED = "inferred"


@dataclass(frozen=True, slots=True)
class ProvenancedValue:
    value: str
    source: MetadataSource
    confidence: float


def record_metadata_value(
    value: str, *, source: MetadataSource, confidence: float
) -> ProvenancedValue:
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be in [0,1]")
    return ProvenancedValue(value=value, source=source, confidence=confidence)
