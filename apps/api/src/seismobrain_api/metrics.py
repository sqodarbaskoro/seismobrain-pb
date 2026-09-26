"""
File: metrics.py
Description: Prometheus metrics registry for §14.2 (Starter /metrics)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-16
Version: 0.2.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

REGISTRY = CollectorRegistry()

CHUNK_OVERFLOW_TOTAL = Counter(
    "sb_chunk_overflow_total",
    "Chunk text overflows that would otherwise silently truncate (must stay 0)",
    labelnames=("model",),
    registry=REGISTRY,
)
CHUNK_OVERFLOW_TOTAL.labels(model="default")

CHAT_LATENCY = Histogram(
    "sb_chat_latency_seconds",
    "Chat end-to-end latency",
    labelnames=("route", "mode", "locality"),
    registry=REGISTRY,
)
CHAT_LATENCY.labels(route="doc_qa", mode="balanced", locality="local")

TTFT = Histogram(
    "sb_ttft_seconds",
    "Time to first token",
    labelnames=("provider", "model"),
    registry=REGISTRY,
)
TTFT.labels(provider="ollama_vllm", model="default")

RETRIEVAL_LATENCY = Histogram(
    "sb_retrieval_latency_seconds",
    "Retrieval latency by arm",
    labelnames=("arm",),
    registry=REGISTRY,
)
RETRIEVAL_LATENCY.labels(arm="dense")

RERANK_LATENCY = Histogram(
    "sb_rerank_latency_seconds",
    "Rerank latency",
    labelnames=("model",),
    registry=REGISTRY,
)
RERANK_LATENCY.labels(model="default")

REFUSALS_TOTAL = Counter(
    "sb_refusals_total",
    "Typed refusals",
    labelnames=("type",),
    registry=REGISTRY,
)
REFUSALS_TOTAL.labels(type="insufficient_evidence")

SENTENCES_TOTAL = Counter(
    "sb_sentences_total",
    "Verified sentences",
    labelnames=("support", "mode", "stage"),
    registry=REGISTRY,
)
SENTENCES_TOTAL.labels(support="supported", mode="balanced", stage="final")

ACL_GUARD_DROPPED = Counter(
    "sb_acl_guard_dropped_total",
    "Candidates dropped by authorization/version guard",
    labelnames=("reason",),
    registry=REGISTRY,
)
ACL_GUARD_DROPPED.labels(reason="acl")

SSE_REPLAYS = Counter(
    "sb_sse_replays_total",
    "SSE reconnect outcomes",
    labelnames=("outcome",),
    registry=REGISTRY,
)
SSE_REPLAYS.labels(outcome="replayed")

EXTERNAL_LLM_CALLS = Counter(
    "sb_external_llm_calls_total",
    "External LLM calls through egress gateway",
    labelnames=("provider",),
    registry=REGISTRY,
)
EXTERNAL_LLM_CALLS.labels(provider="openai_compatible")

FEEDBACK_TOTAL = Counter(
    "sb_feedback_total",
    "User feedback",
    labelnames=("rating", "reason"),
    registry=REGISTRY,
)
FEEDBACK_TOTAL.labels(rating="down", reason="wrong")

ACL_SYNC_LAG = Gauge(
    "sb_acl_sync_lag_seconds",
    "ACL sync lag",
    registry=REGISTRY,
)
ACL_SYNC_LAG.set(0)

INDEX_MISMATCHES = Gauge(
    "sb_index_consistency_mismatches",
    "Index consistency mismatches",
    labelnames=("collection",),
    registry=REGISTRY,
)
INDEX_MISMATCHES.labels(collection="default").set(0)

INGESTION_JOBS = Gauge(
    "sb_ingestion_jobs",
    "Ingestion jobs by status",
    labelnames=("status",),
    registry=REGISTRY,
)
INGESTION_JOBS.labels(status="queued").set(0)


def render_metrics() -> bytes:
    return generate_latest(REGISTRY)
