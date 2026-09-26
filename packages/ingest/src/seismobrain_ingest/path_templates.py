"""
File: path_templates.py
Description: Path templates map folder structure to metadata (FR-DOC-07)
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

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PathTemplateResult:
    matched: bool
    fields: dict[str, str]


def apply_path_template(path: str, template: str) -> PathTemplateResult:
    """
    Map a filesystem path using a template with {field} placeholders.
    Example template: '{plant}/{doc_type}/{title}.pdf'
    """
    pattern = re.escape(template)
    pattern = re.sub(r"\\\{(\w+)\\\}", r"(?P<\1>[^/]+)", pattern)
    pattern = pattern.replace(r"\*", "[^/]*")
    match = re.fullmatch(pattern, path.strip("/"))
    if not match:
        return PathTemplateResult(matched=False, fields={})
    return PathTemplateResult(matched=True, fields=dict(match.groupdict()))
