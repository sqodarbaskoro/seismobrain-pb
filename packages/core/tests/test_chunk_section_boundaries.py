"""
File: test_chunk_section_boundaries.py
Description: FR-CHK-01 — chunks never cross section boundaries (property test)
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

from hypothesis import given, settings
from hypothesis import strategies as st

from seismobrain_core.chunking import SectionInput, chunk_document


@given(
    st.lists(
        st.tuples(
            st.text(min_size=1, max_size=12, alphabet=st.characters(whitelist_categories=("L",))),
            st.lists(
                st.text(
                    min_size=5,
                    max_size=40,
                    alphabet=st.characters(whitelist_categories=("L", "Z")),
                ),
                min_size=1,
                max_size=4,
            ),
        ),
        min_size=1,
        max_size=5,
    )
)
@settings(max_examples=40)
def test_chunks_never_cross_section_boundaries(
    sections_data: list[tuple[str, list[str]]],
) -> None:
    sections = [
        SectionInput(
            section_id=f"s{index}",
            heading_path=(title,),
            paragraphs=tuple(f"{para}." for para in paras),
        )
        for index, (title, paras) in enumerate(sections_data)
    ]
    result = chunk_document(sections, document_title="Doc", child_max_tokens=12)
    for chunk in result.children:
        assert chunk.section_id in {s.section_id for s in sections}
        # Text belongs only to its section's paragraph pool.
        section = next(s for s in sections if s.section_id == chunk.section_id)
        joined = " ".join(section.paragraphs)
        for token in chunk.text.replace(".", " ").split():
            assert token in joined
