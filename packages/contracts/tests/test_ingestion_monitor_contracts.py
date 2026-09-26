"""The generated API describes typed job summaries, history, and real actions."""

import json
from pathlib import Path


def test_ingestion_openapi_contract() -> None:
    schema = json.loads((Path(__file__).resolve().parents[3] / "openapi/openapi.json").read_text())
    base = "/api/v1/admin/ingestion"
    for path in ["/monitor", "/jobs", "/jobs/{job_id}"]:
        assert schema["paths"][base + path]["get"]["responses"]["200"]["content"][
            "application/json"
        ]
    for action in ["retry", "quarantine", "release"]:
        assert "post" in schema["paths"][base + "/jobs/{job_id}/" + action]
    props = schema["components"]["schemas"]["IngestionJob"]["properties"]
    assert {"events", "attempts", "error", "filename", "status", "actions"} <= props.keys()
    assert "payload" not in props
