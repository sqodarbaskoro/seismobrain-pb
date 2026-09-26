/**
 * @file chat-history.ts
 * @description Restore chat turns and citation metadata from saved messages
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-18
 * @modified 2026-09-18
 * @version 0.1.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import type { ChatSentence, CitationMeta } from "./chat-answer";

/** Real retrieval facts from the server's `trace` SSE event, for "Why this answer" —
 * only available for a turn just sent in this session (SSE-only, not persisted with
 * the message), so it's null for anything restored from conversation history. */
export type ChatTrace = {
  resolvedQuery: string;
  route: string;
  collectionIds: string[] | null;
  evidenceCount: number;
  latencyMs: number;
};

export type Turn = {
  question: string;
  sentences: ChatSentence[];
  citations: Record<string, CitationMeta>;
  evidenceText: Record<string, string>;
  /** Typed refusal reason (e.g. "no_evidence"), or null for an answered turn. */
  refusalType: string | null;
  /** The assistant message id this turn resolved to, once it has one. */
  messageId: string | null;
  trace: ChatTrace | null;
};

export type ConversationHistory = {
  id: string;
  title: string;
  messages: {
    id: string;
    role: string;
    content: string;
    refusal_type?: string | null;
    answer: { text: string; citations: string[]; support: string }[];
    citations: Record<string, CitationMeta>;
  }[];
};

export function restoreHistory(history: ConversationHistory) {
  const turns: Turn[] = [];
  let lastMessageId: string | null = null;
  for (const message of history.messages) {
    if (message.role === "user") {
      turns.push({
        question: message.content,
        sentences: [],
        citations: {},
        evidenceText: {},
        refusalType: null,
        messageId: null,
        trace: null,
      });
    } else if (message.role === "assistant" && turns.length) {
      const turn = turns[turns.length - 1];
      turn.citations = message.citations;
      turn.evidenceText = Object.fromEntries(
        Object.values(message.citations).map((meta) => [
          meta.evidence_id, meta.text || `${meta.title} ${meta.section ?? ""}`.trim(),
        ]),
      );
      turn.sentences = message.answer.length
        ? message.answer.map((part) => ({
            text: part.text,
            support: part.support,
            evidence: part.citations.map((id) => message.citations[id]?.evidence_id ?? id),
          }))
        : [{ text: message.content, evidence: [], support: message.refusal_type ?? "unsupported" }];
      turn.refusalType = message.refusal_type ?? null;
      turn.messageId = message.id;
      lastMessageId = message.id;
    }
  }
  return { turns, lastMessageId };
}
