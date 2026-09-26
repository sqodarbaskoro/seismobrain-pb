"""
File: test_parse_fixtures_p1.py
Description: P1 parse fixtures via plugins (T5.11)
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

import io
import zipfile

from seismobrain_ingest.parsers_p1 import build_p1_registry


def test_p1_plugins_parse_fixtures() -> None:
    registry = build_p1_registry()
    html = registry.parse("note.html", b"<html><title>Note</title><body>Hello</body></html>")
    assert html.format == "html"
    assert "Hello" in html.nodes[0].text

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("ppt/slides/slide1.xml", "<a:t>Slide text</a:t>")
    pptx = registry.parse("deck.pptx", buf.getvalue())
    assert pptx.format == "pptx"
    assert "Slide text" in pptx.nodes[0].text

    rtf = registry.parse("a.rtf", b"{\\rtf1 Torque is 40}")
    assert rtf.format == "rtf"
    assert "Torque" in rtf.nodes[0].text
