"""
File: test_embed_rerank_verify_endpoints.py
Description: Models service HTTP endpoints for embed/sparse/rerank/verify (T0c.9)
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

from fastapi.testclient import TestClient

from seismobrain_adapters.models.http_gateway import HttpModelGateway
from seismobrain_models.app import create_models_app


def test_embed_sparse_rerank_verify_endpoints() -> None:
    client = TestClient(create_models_app())
    embed = client.post(
        "/v1/embed", json={"texts": ["alpha", "beta"], "model_id": "cpu-hash"}
    )
    assert embed.status_code == 200
    vectors = embed.json()["vectors"]
    assert len(vectors) == 2
    assert len(vectors[0]) == 32

    sparse = client.post(
        "/v1/sparse", json={"texts": ["well alpha-1"], "model_id": "cpu-sparse"}
    )
    assert sparse.status_code == 200
    assert sparse.json()["vectors"][0]["indices"]
    assert sparse.json()["vectors"][0]["values"]

    rerank = client.post(
        "/v1/rerank",
        json={
            "query": "alpha",
            "documents": ["zzz", "alpha well", "beta"],
            "model_id": "cpu-rerank",
        },
    )
    assert rerank.status_code == 200
    order = rerank.json()["indices"]
    assert order[0] == 1

    verify = client.post(
        "/v1/verify",
        json={
            "claim": "limit is 6 knots",
            "evidence": "The normal limit is 6 knots.",
            "model_id": "cpu-verify",
        },
    )
    assert verify.status_code == 200
    assert verify.json()["label"] in {
        "supported",
        "partial",
        "unsupported",
        "no_citation",
    }


def test_http_gateway_calls_models_service() -> None:
    app = create_models_app()
    with TestClient(app) as client:
        gateway = HttpModelGateway(base_url=str(client.base_url), http_client=client)
        vectors = gateway.embed(["hello"], model_id="cpu-hash")
        assert len(vectors[0]) == 32
        order = gateway.rerank("q", ["a", "q match"], model_id="cpu-rerank")
        assert order[0] == 1
        label = gateway.verify("a", "a is true", model_id="cpu-verify")
        assert isinstance(label, str)
