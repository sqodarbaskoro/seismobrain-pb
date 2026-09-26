"""
File: test_k8s_network_policies.py
Description: Production NetworkPolicies and air-gapped egress (T6.3)
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

ROOT = Path(__file__).resolve().parents[1]
NP = ROOT / "helm" / "seismobrain" / "templates" / "networkpolicy.yaml"
VALUES_CI = ROOT / "helm" / "seismobrain" / "values.ci.yaml"


def test_default_deny_egress_with_explicit_allows() -> None:
    text = NP.read_text(encoding="utf-8")
    assert "seismobrain-default-deny-egress" in text
    assert "policyTypes:" in text
    assert "- Egress" in text
    assert "port: 53" in text
    assert "port: 5432" in text
    assert "port: 6333" in text
    # Air-gapped path omits open HTTPS unless egress-gateway
    assert "airGapped" in text
    assert "egress-gateway" in text


def test_ci_values_enable_air_gapped_network_policy() -> None:
    text = VALUES_CI.read_text(encoding="utf-8")
    assert "airGapped: true" in text
    assert "enabled: true" in text
