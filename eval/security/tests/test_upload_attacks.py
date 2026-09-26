"""
File: test_upload_attacks.py
Description: Upload attack defenses in security suite (T4.28)
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

from seismobrain_core.upload_guards import reject_dangerous_upload


def test_rejects_zip_bomb_and_macro_office() -> None:
    assert reject_dangerous_upload(
        filename="doc.xlsm", content_type="application/vnd.ms-excel.sheet.macroEnabled.12", size=100
    )
    assert reject_dangerous_upload(
        filename="bomb.zip", content_type="application/zip", size=50 * 1024 * 1024 * 1024
    )
    assert not reject_dangerous_upload(
        filename="safe.pdf", content_type="application/pdf", size=1024
    )
