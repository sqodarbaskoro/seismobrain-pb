"""
File: test_answerability_gate_trained.py
Description: Trained answerability gate global base (T5.8)
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

import pytest

from seismobrain_core.answerability import EvidenceSnippet
from seismobrain_core.answerability_trained import (
    GateModelCard,
    assert_global_base_training,
    trained_answerability,
)


def test_trained_gate_uses_public_synthetic_only() -> None:
    card = GateModelCard(
        model_id="gate-global-v1",
        training_corpus="public_or_synthetic",
        tenant_private_data=False,
    )
    assert_global_base_training(card)
    decision = trained_answerability(
        "torque for P2/94",
        [EvidenceSnippet("Torque is 40 Nm for flange P2/94", 0.9)],
        card=card,
        threshold=0.4,
    )
    assert decision.answerable is True

    with pytest.raises(ValueError, match="tenant private"):
        assert_global_base_training(
            GateModelCard(
                model_id="bad",
                training_corpus="public",
                tenant_private_data=True,
            )
        )
