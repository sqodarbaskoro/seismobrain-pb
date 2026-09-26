import pytest
from pydantic import ValidationError

from seismobrain_core.ingestion_jobs import IngestionJob, allowed_actions


def test_recovery_actions_follow_job_state() -> None:
    assert allowed_actions("succeeded") == []
    assert allowed_actions("running") == ["quarantine"]
    assert allowed_actions("quarantined") == ["release"]
    assert "retry" in allowed_actions("dead_letter")
    assert "retry" not in allowed_actions("pending")
    with pytest.raises(ValidationError):
        IngestionJob.model_validate({"id": "j", "created_at": 1, "updated_at": 1, "status": "fake"})
