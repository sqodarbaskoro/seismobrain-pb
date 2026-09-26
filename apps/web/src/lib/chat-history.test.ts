/**
 * @file chat-history.test.ts
 * @description Saved conversations restore answers, citations, refusals, and copy targets
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-18
 * @modified 2026-09-18
 * @version 0.1.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { expect, it } from "vitest";
import { restoreHistory, type ConversationHistory } from "./chat-history";

it("restores multiple turns with source links and refusal text", () => {
  const history: ConversationHistory = {
    id: "one", title: "Torque",
    messages: [
      { id: "q1", role: "user", content: "What is torque?", answer: [], citations: {} },
      {
        id: "a1", role: "assistant", content: "Torque is 40 Nm.",
        answer: [{ text: "Torque is 40 Nm.", citations: ["C1"], support: "supported" }],
        citations: { C1: { evidence_id: "E5", title: "Ops Manual", section: "4.2", page: 12 } },
      },
      { id: "q2", role: "user", content: "And pressure?", answer: [], citations: {} },
      {
        id: "a2", role: "assistant", content: "No evidence found.",
        answer: [], citations: {}, refusal_type: "no_evidence",
      },
    ],
  };
  const restored = restoreHistory(history);
  expect(restored.turns.map((turn) => turn.question)).toEqual(["What is torque?", "And pressure?"]);
  expect(restored.turns[0].sentences[0].evidence).toEqual(["E5"]);
  expect(restored.turns[0].citations.C1.page).toBe(12);
  expect(restored.turns[0].evidenceText.E5).toBe("Ops Manual 4.2");
  expect(restored.turns[1].sentences).toEqual([
    { text: "No evidence found.", evidence: [], support: "no_evidence" },
  ]);
  expect(restored.lastMessageId).toBe("a2");
  expect(restoreHistory({ id: "new", title: "New chat", messages: [] })).toEqual({
    turns: [], lastMessageId: null,
  });
});
