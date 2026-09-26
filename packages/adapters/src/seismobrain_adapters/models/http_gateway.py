"""
File: http_gateway.py
Description: HTTP ModelGateway client for the Team models service (T0c.9)
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

from typing import Any, Protocol

import httpx

from seismobrain_core.ports import ModelGatewayKind


class _HttpClient(Protocol):
    def post(self, url: str, *, json: dict[str, Any] | None = None) -> Any: ...


class HttpModelGateway:
    """Team ModelGateway calling the models service over HTTP."""

    def __init__(
        self, base_url: str, *, http_client: _HttpClient | None = None
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = http_client

    @property
    def kind(self) -> ModelGatewayKind:
        return ModelGatewayKind.HTTP

    @property
    def base_url(self) -> str:
        return self._base_url

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        if self._client is not None:
            response = self._client.post(url, json=payload)
            response.raise_for_status()
            return dict(response.json())
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            return dict(response.json())

    def embed(self, texts: list[str], *, model_id: str) -> list[list[float]]:
        body = self._post("/v1/embed", {"texts": texts, "model_id": model_id})
        return [list(map(float, row)) for row in body["vectors"]]

    def rerank(
        self, query: str, documents: list[str], *, model_id: str
    ) -> list[int]:
        body = self._post(
            "/v1/rerank",
            {"query": query, "documents": documents, "model_id": model_id},
        )
        return [int(i) for i in body["indices"]]

    def verify(self, claim: str, evidence: str, *, model_id: str) -> str:
        body = self._post(
            "/v1/verify",
            {"claim": claim, "evidence": evidence, "model_id": model_id},
        )
        return str(body["label"])
