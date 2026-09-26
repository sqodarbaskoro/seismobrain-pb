"""
File: test_chunk_no_truncation.py
Description: FR-CHK-04 — tokenizer length; overflow split; never truncate
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

from seismobrain_core.chunking import SectionInput, chunk_document


def test_overflow_splits_without_truncation() -> None:
    long_para = " ".join(f"Word{i}." for i in range(80))
    section = SectionInput(
        section_id="s1",
        heading_path=("Body",),
        paragraphs=(long_para,),
    )
    result = chunk_document([section], document_title="Doc", child_max_tokens=15)
    assert result.truncations == 0
    assert result.overflow_splits >= 1
    joined = " ".join(c.text for c in result.children)
    for i in range(80):
        assert f"Word{i}." in joined
