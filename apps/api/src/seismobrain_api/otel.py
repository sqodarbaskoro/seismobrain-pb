"""
File: otel.py
Description: Per-message OpenTelemetry span names and in-process tracer (PRD §14.1)
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

import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field

MESSAGE_SPANS = (
    "route",
    "rewrite",
    "embed.dense",
    "embed.sparse",
    "vector.query",
    "fusion",
    "rerank",
    "gate",
    "select",
    "expand",
    "context.build",
    "llm.generate",
    "verify",
    "numeric_check",
    "render",
    "persist",
)


@dataclass
class SpanRecord:
    name: str
    attributes: dict[str, object] = field(default_factory=dict)


@dataclass
class MessageTrace:
    trace_id: str
    spans: list[SpanRecord] = field(default_factory=list)

    def record(self, name: str, **attributes: object) -> None:
        if name not in MESSAGE_SPANS:
            raise ValueError(f"unknown message span: {name}")
        self.spans.append(SpanRecord(name=name, attributes=dict(attributes)))


@dataclass
class InMemoryTracer:
    traces: dict[str, MessageTrace] = field(default_factory=dict)

    def start_message_trace(self) -> MessageTrace:
        trace_id = uuid.uuid4().hex
        trace = MessageTrace(trace_id=trace_id)
        self.traces[trace_id] = trace
        return trace

    @contextmanager
    def span(self, trace: MessageTrace, name: str, **attributes: object) -> Iterator[None]:
        trace.record(name, **attributes)
        yield
