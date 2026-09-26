"""
File: conversations.py
Description: In-memory conversation and message store with ownership (FR-CHAT-01)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-18
Version: 0.4.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


def title_from_question(question: str) -> str:
    title = " ".join(question.split())
    if len(title) <= 48:
        return title or "New chat"
    prefix = title[:45]
    if not title[45].isspace() and " " in prefix:
        prefix = prefix.rsplit(" ", 1)[0]
    return prefix.rstrip() + "..."


@dataclass
class MessageRecord:
    id: str
    conversation_id: str
    role: str
    content: str
    status: str = "final"
    route: str | None = None
    refusal_type: str | None = None
    answer: list[dict[str, Any]] = field(default_factory=list)
    citations: dict[str, Any] = field(default_factory=dict)
    grounding_summary_pre: dict[str, Any] = field(default_factory=dict)
    grounding_summary_final: dict[str, Any] = field(default_factory=dict)
    generation_record: dict[str, Any] = field(default_factory=dict)
    evidence_snapshot_uris: dict[str, str] = field(default_factory=dict)


@dataclass
class ConversationRecord:
    id: str
    user_id: str
    workspace_id: str
    title: str
    archived: bool = False
    messages: list[MessageRecord] = field(default_factory=list)

    def add_message(self, message: MessageRecord) -> None:
        if (
            message.role == "user"
            and self.title == "New chat"
            and not any(m.role == "user" for m in self.messages)
        ):
            self.title = title_from_question(message.content)
        self.messages.append(message)


class ConversationStore:
    def __init__(self) -> None:
        self._conversations: dict[str, ConversationRecord] = {}

    def create(
        self, *, user_id: str, workspace_id: str, title: str = "New chat"
    ) -> ConversationRecord:
        conv_id = f"conv_{uuid.uuid4().hex[:12]}"
        record = ConversationRecord(
            id=conv_id, user_id=user_id, workspace_id=workspace_id, title=title
        )
        self._conversations[conv_id] = record
        return record

    def get(self, conversation_id: str) -> ConversationRecord | None:
        return self._conversations.get(conversation_id)

    def require_owner(
        self, conversation_id: str, user_id: str
    ) -> ConversationRecord:
        record = self.get(conversation_id)
        if record is None or record.user_id != user_id:
            raise PermissionError("conversation not found or not owned")
        return record

    def rename(self, conversation_id: str, user_id: str, title: str) -> ConversationRecord:
        record = self.require_owner(conversation_id, user_id)
        record.title = title
        return record

    def delete(self, conversation_id: str, user_id: str) -> None:
        self.require_owner(conversation_id, user_id)
        del self._conversations[conversation_id]

    def search(self, user_id: str, *, q: str = "") -> list[ConversationRecord]:
        needle = q.lower().strip()
        out = [
            c
            for c in self._conversations.values()
            if c.user_id == user_id and not c.archived
        ]
        if needle:
            out = [c for c in out if needle in c.title.lower()]
        return list(reversed(out))

    def add_message(
        self, conversation_id: str, user_id: str, message: MessageRecord
    ) -> MessageRecord:
        record = self.require_owner(conversation_id, user_id)
        record.add_message(message)
        return message

    def set_message_status(
        self, conversation_id: str, message_id: str, user_id: str, status: str
    ) -> MessageRecord | None:
        message = self.get_message(conversation_id, message_id, user_id)
        if message is not None:
            message.status = status
        return message

    def get_message(
        self, conversation_id: str, message_id: str, user_id: str
    ) -> MessageRecord | None:
        record = self.require_owner(conversation_id, user_id)
        for msg in record.messages:
            if msg.id == message_id:
                return msg
        return None

    def new_message_id(self) -> str:
        return f"msg_{uuid.uuid4().hex[:12]}"
