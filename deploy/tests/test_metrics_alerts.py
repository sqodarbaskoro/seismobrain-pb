"""
File: test_metrics_alerts.py
Description: Dashboards/alert rules and §14.2 metric names (T4.20)
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

from pathlib import Path

import yaml

from seismobrain_api.metrics import render_metrics

ROOT = Path(__file__).resolve().parents[1]
OBS = ROOT / "observability"


def test_dashboards_and_alert_rules_present() -> None:
    dashboard = OBS / "dashboards" / "overview.json"
    alerts = OBS / "alerts.yml"
    assert dashboard.is_file()
    assert alerts.is_file()
    data = yaml.safe_load(alerts.read_text(encoding="utf-8"))
    names = {r["alert"] for g in data["groups"] for r in g["rules"]}
    assert "ChatLatencyHigh" in names
    assert "ChunkOverflow" in names
    assert "EgressBlocked" in names
    text = dashboard.read_text(encoding="utf-8")
    assert "sb_chat_latency_seconds" in text
    assert "Governance" in text


def test_section_14_2_metrics_exported() -> None:
    body = render_metrics().decode()
    for name in (
        "sb_chat_latency_seconds",
        "sb_ttft_seconds",
        "sb_retrieval_latency_seconds",
        "sb_rerank_latency_seconds",
        "sb_refusals_total",
        "sb_sentences_total",
        "sb_acl_guard_dropped_total",
        "sb_sse_replays_total",
        "sb_chunk_overflow_total",
        "sb_external_llm_calls_total",
        "sb_feedback_total",
        "sb_acl_sync_lag_seconds",
        "sb_index_consistency_mismatches",
        "sb_ingestion_jobs",
    ):
        assert name in body
