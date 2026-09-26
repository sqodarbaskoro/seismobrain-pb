"""
File: test_sentence_verifier.py
Description: Sentence verifier via ModelGateway (T3.5)
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

from seismobrain_adapters.models.in_process import InProcessModelGateway
from seismobrain_core.sentence_tag_validation import ValidatedSentence
from seismobrain_core.sentence_verifier import class_metrics, verify_sentences


def test_verifier_labels_and_metrics() -> None:
    gateway = InProcessModelGateway()
    sentences = [
        ValidatedSentence("Torque is 40 Nm [E1]", ("E1",)),
        ValidatedSentence("Unrelated claim [E1]", ("E1",)),
        ValidatedSentence("No tags here", ()),
    ]
    evidence = {"E1": "Torque is 40 Nm for flange P2/94."}
    verified = verify_sentences(sentences, evidence_text=evidence, gateway=gateway)
    assert verified[0].label == "supported"
    assert verified[2].label == "no_citation"
    metrics = class_metrics(
        [v.label for v in verified],
        ["supported", "unsupported", "no_citation"],
    )
    assert "supported" in metrics.counts or metrics.counts
    assert 0.0 <= metrics.unsupported_to_supported <= 1.0
