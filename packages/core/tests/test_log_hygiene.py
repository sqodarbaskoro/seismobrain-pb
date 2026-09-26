"""
File: test_log_hygiene.py
Description: Log hygiene — no secrets, prompts, or document text by default (SEC-20)
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

import logging

import pytest

from seismobrain_core.log_hygiene import SafeLogFilter, redact_mapping


def test_redacts_secrets_prompts_and_document_text() -> None:
    payload = {
        "user_id": "u1",
        "password": "super-secret",
        "jwt_secret": "abc",
        "prompt": "SYSTEM: do not leak",
        "document_text": "confidential paragraph",
        "evidence_text": "chunk body",
        "ok": True,
    }
    cleaned = redact_mapping(payload)
    assert cleaned["user_id"] == "u1"
    assert cleaned["password"] == "[REDACTED]"
    assert cleaned["jwt_secret"] == "[REDACTED]"
    assert cleaned["prompt"] == "[REDACTED]"
    assert cleaned["document_text"] == "[REDACTED]"
    assert cleaned["evidence_text"] == "[REDACTED]"
    assert cleaned["ok"] is True


def test_filter_blocks_sensitive_log_records(
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger = logging.getLogger("seismobrain.test.hygiene")
    logger.addFilter(SafeLogFilter())
    with caplog.at_level(logging.INFO, logger=logger.name):
        logger.info("login ok user=%s password=%s", "u1", "secret")
        logger.info("trace prompt=%s", "do-not-log")
    assert caplog.records == []


def test_llm_trace_opt_in_allows_prompt_when_enabled(
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger = logging.getLogger("seismobrain.test.hygiene.trace")
    logger.addFilter(SafeLogFilter(llm_trace_enabled=True))
    with caplog.at_level(logging.INFO, logger=logger.name):
        logger.info("trace prompt=%s", "allowed-when-opted-in")
    assert len(caplog.records) == 1
