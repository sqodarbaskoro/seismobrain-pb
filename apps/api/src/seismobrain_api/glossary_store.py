"""
File: glossary_store.py
Description: Workspace glossary and identifier-pattern editor store (FR-ADM-10)
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

from dataclasses import dataclass, field


@dataclass
class GlossaryEntry:
    term: str
    expansion: str


@dataclass
class IdentifierPattern:
    name: str
    pattern: str
    confidence: str = "high"


@dataclass
class WorkspaceGlossary:
    entries: list[GlossaryEntry] = field(default_factory=list)
    identifier_patterns: list[IdentifierPattern] = field(default_factory=list)


@dataclass
class GlossaryStore:
    workspaces: dict[str, WorkspaceGlossary] = field(default_factory=dict)

    def _ws(self, workspace_id: str) -> WorkspaceGlossary:
        if workspace_id not in self.workspaces:
            self.workspaces[workspace_id] = WorkspaceGlossary()
        return self.workspaces[workspace_id]

    def set_glossary(
        self, workspace_id: str, entries: list[GlossaryEntry]
    ) -> WorkspaceGlossary:
        ws = self._ws(workspace_id)
        ws.entries = list(entries)
        return ws

    def set_identifier_patterns(
        self, workspace_id: str, patterns: list[IdentifierPattern]
    ) -> WorkspaceGlossary:
        ws = self._ws(workspace_id)
        ws.identifier_patterns = list(patterns)
        return ws

    def as_public(self, workspace_id: str) -> dict[str, object]:
        ws = self._ws(workspace_id)
        return {
            "workspace_id": workspace_id,
            "glossary": [{"term": e.term, "expansion": e.expansion} for e in ws.entries],
            "identifier_patterns": [
                {
                    "name": p.name,
                    "pattern": p.pattern,
                    "confidence": p.confidence,
                }
                for p in ws.identifier_patterns
            ],
        }
