"""
File: feedback_store.py
Description: Feedback thumbs with reasons (FR-FB-01/02)
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

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FeedbackItem:
    id: str
    message_id: str
    rating: str
    reason: str
    comment: str = ""
    promoted_case_id: str | None = None


@dataclass
class FeedbackStore:
    items: dict[str, FeedbackItem] = field(default_factory=dict)
    draft_cases: dict[str, dict[str, Any]] = field(default_factory=dict)

    def add(
        self,
        *,
        message_id: str,
        rating: str,
        reason: str,
        comment: str = "",
    ) -> FeedbackItem:
        item = FeedbackItem(
            id=f"fb_{uuid.uuid4().hex[:10]}",
            message_id=message_id,
            rating=rating,
            reason=reason,
            comment=comment,
        )
        self.items[item.id] = item
        return item

    def promote(self, feedback_id: str, *, actor: str) -> dict[str, Any]:
        item = self.items[feedback_id]
        case_id = f"case_{uuid.uuid4().hex[:8]}"
        draft = {
            "id": case_id,
            "from_feedback": feedback_id,
            "message_id": item.message_id,
            "reason": item.reason,
            "comment": item.comment,
            "status": "draft",
            "promoted_by": actor,
        }
        self.draft_cases[case_id] = draft
        item.promoted_case_id = case_id
        return draft
