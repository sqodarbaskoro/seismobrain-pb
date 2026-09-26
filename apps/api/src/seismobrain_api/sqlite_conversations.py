"""
File: sqlite_conversations.py
Description: Durable Starter conversation history with transactional SQLite updates
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-18
Modified: 2026-09-18
Version: 0.2.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import closing, contextmanager
from dataclasses import asdict
from pathlib import Path

from seismobrain_api.conversations import (
    ConversationRecord,
    ConversationStore,
    MessageRecord,
    title_from_question,
)


class SqliteConversationStore(ConversationStore):
    """Read from disk on every access; serialize changes to avoid lost messages."""

    def __init__(self, path: Path) -> None:
        self._path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn, conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                """CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    payload TEXT NOT NULL
                )"""
            )
            conn.execute("CREATE INDEX IF NOT EXISTS conversations_owner ON conversations(user_id)")
            # Repair placeholder titles left by older servers without changing custom names.
            rows = conn.execute(
                "SELECT payload FROM conversations WHERE json_extract(payload, '$.title') = ?",
                ("New chat",),
            ).fetchall()
            for row in rows:
                record = self._decode(row[0])
                first_question = next(
                    (m.content for m in record.messages if m.role == "user"), None
                )
                if first_question:
                    record.title = title_from_question(first_question)
                    conn.execute(
                        "UPDATE conversations SET payload = ? WHERE id = ?",
                        (json.dumps(asdict(record)), record.id),
                    )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path, timeout=30)

    @staticmethod
    def _decode(payload: str) -> ConversationRecord:
        data = json.loads(payload)
        messages = [MessageRecord(**m) for m in data.pop("messages")]
        return ConversationRecord(**data, messages=messages)

    @contextmanager
    def _update(self, conversation_id: str, user_id: str) -> Iterator[ConversationRecord]:
        with closing(self._connect()) as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT payload FROM conversations WHERE id = ? AND user_id = ?",
                (conversation_id, user_id),
            ).fetchone()
            if row is None:
                raise PermissionError("conversation not found or not owned")
            record = self._decode(row[0])
            yield record
            conn.execute(
                "UPDATE conversations SET payload = ? WHERE id = ?",
                (json.dumps(asdict(record)), conversation_id),
            )

    def create(
        self, *, user_id: str, workspace_id: str, title: str = "New chat"
    ) -> ConversationRecord:
        record = ConversationRecord(
            id=f"conv_{uuid.uuid4().hex[:12]}", user_id=user_id,
            workspace_id=workspace_id, title=title,
        )
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT INTO conversations(id, user_id, payload) VALUES (?, ?, ?)",
                (record.id, record.user_id, json.dumps(asdict(record))),
            )
        return record

    def get(self, conversation_id: str) -> ConversationRecord | None:
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT payload FROM conversations WHERE id = ?", (conversation_id,),
            ).fetchone()
        return self._decode(row[0]) if row else None

    def search(self, user_id: str, *, q: str = "") -> list[ConversationRecord]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT payload FROM conversations WHERE user_id = ? ORDER BY rowid DESC",
                (user_id,),
            ).fetchall()
        records = [self._decode(row[0]) for row in rows]
        needle = q.lower().strip()
        return [c for c in records if not c.archived and needle in c.title.lower()]

    def rename(self, conversation_id: str, user_id: str, title: str) -> ConversationRecord:
        with self._update(conversation_id, user_id) as record:
            record.title = title
        return record

    def delete(self, conversation_id: str, user_id: str) -> None:
        with closing(self._connect()) as conn, conn:
            deleted = conn.execute(
                "DELETE FROM conversations WHERE id = ? AND user_id = ?",
                (conversation_id, user_id),
            )
            if deleted.rowcount == 0:
                raise PermissionError("conversation not found or not owned")

    def add_message(
        self, conversation_id: str, user_id: str, message: MessageRecord
    ) -> MessageRecord:
        with self._update(conversation_id, user_id) as record:
            record.add_message(message)
        return message

    def set_message_status(
        self, conversation_id: str, message_id: str, user_id: str, status: str
    ) -> MessageRecord | None:
        with self._update(conversation_id, user_id) as record:
            message = next((m for m in record.messages if m.id == message_id), None)
            if message is not None:
                message.status = status
        return message
