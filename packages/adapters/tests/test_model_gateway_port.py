"""
File: test_model_gateway_port.py
Description: ModelGateway port interface tests (in-process and HTTP stubs)
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

from seismobrain_adapters.models.http_gateway import HttpModelGateway
from seismobrain_adapters.models.in_process import InProcessModelGateway
from seismobrain_core.ports import ModelGateway, ModelGatewayKind


def _assert_gateway_contract(gateway: ModelGateway) -> None:
    assert gateway.kind in {ModelGatewayKind.IN_PROCESS, ModelGatewayKind.HTTP}
    vectors = gateway.embed(["hello"], model_id="stub-embed")
    assert len(vectors) == 1
    assert len(vectors[0]) > 0
    ranked = gateway.rerank("q", ["a", "b"], model_id="stub-rerank")
    assert ranked == [0, 1] or set(ranked) == {0, 1}
    label = gateway.verify("claim", "evidence", model_id="stub-verify")
    assert label in {"supported", "partial", "unsupported", "no_citation", "neutral"}


def test_in_process_model_gateway_port() -> None:
    gateway: ModelGateway = InProcessModelGateway()
    assert gateway.kind == ModelGatewayKind.IN_PROCESS
    _assert_gateway_contract(gateway)


def test_http_model_gateway_port_uses_base_url() -> None:
    gateway = HttpModelGateway(base_url="http://models:8081")
    assert gateway.kind == ModelGatewayKind.HTTP
    assert gateway.base_url == "http://models:8081"
