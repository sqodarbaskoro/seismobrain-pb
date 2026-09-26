"""
File: app.py
Description: FastAPI models service exposing embed/sparse/rerank/verify (T0c.9)
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

from fastapi import FastAPI
from pydantic import BaseModel, Field

from seismobrain_models.config import ModelsSettings
from seismobrain_models.runtime import dense_embed, rerank, sparse_encode, verify_claim


class EmbedRequest(BaseModel):
    texts: list[str] = Field(min_length=1)
    model_id: str = "cpu-hash"


class SparseRequest(BaseModel):
    texts: list[str] = Field(min_length=1)
    model_id: str = "cpu-sparse"


class RerankRequest(BaseModel):
    query: str
    documents: list[str] = Field(min_length=1)
    model_id: str = "cpu-rerank"


class VerifyRequest(BaseModel):
    claim: str
    evidence: str
    model_id: str = "cpu-verify"


def create_models_app(settings: ModelsSettings | None = None) -> FastAPI:
    cfg = settings or ModelsSettings()
    app = FastAPI(title="SeismoBrain Models", version="0.0.0")
    app.state.settings = cfg

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "device": cfg.device}

    @app.post("/v1/embed")
    def embed(body: EmbedRequest) -> dict[str, object]:
        _ = body.model_id
        return {"vectors": dense_embed(body.texts, dim=cfg.embed_dim)}

    @app.post("/v1/sparse")
    def sparse(body: SparseRequest) -> dict[str, object]:
        _ = body.model_id
        return {"vectors": sparse_encode(body.texts)}

    @app.post("/v1/rerank")
    def rerank_route(body: RerankRequest) -> dict[str, object]:
        _ = body.model_id
        return {"indices": rerank(body.query, body.documents)}

    @app.post("/v1/verify")
    def verify_route(body: VerifyRequest) -> dict[str, object]:
        _ = body.model_id
        return {"label": verify_claim(body.claim, body.evidence)}

    return app
