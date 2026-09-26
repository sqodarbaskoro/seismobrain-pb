/**
 * @file chat-answer.test.ts
 * @description Grounded-answer formatting helpers (strip E-tags, citation order)
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-19
 * @version 0.2.1
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { describe, expect, it } from "vitest";
import {
  citationIndexMap,
  citationOrder,
  groupCitationsByDocument,
  groupSentences,
  lookupCitation,
  stripEvidenceTags,
  uniqueSourcesForSentence,
  type ChatSentence,
  type CitationMeta,
} from "./chat-answer";

describe("stripEvidenceTags", () => {
  it("removes trailing evidence markers from a sentence", () => {
    expect(
      stripEvidenceTags(
        "The Device Controller determines the exact trigger time [E5].",
      ),
    ).toBe("The Device Controller determines the exact trigger time.");
  });

  it("removes stacked markers without leaving extra spaces", () => {
    expect(stripEvidenceTags("It assigns a batch number [E6][E7].")).toBe(
      "It assigns a batch number.",
    );
  });
});

describe("citationOrder", () => {
  it("numbers unique evidence in first-appearance order", () => {
    const sentences: ChatSentence[] = [
      { text: "One [E5].", evidence: ["E5"], support: "supported" },
      { text: "Two [E5].", evidence: ["E5"], support: "supported" },
      { text: "Three [E6].", evidence: ["E6"], support: "partial" },
    ];
    const order = citationOrder(sentences);
    expect(order).toEqual(["E5", "E6"]);
    expect(citationIndexMap(order).get("E5")).toBe(1);
    expect(citationIndexMap(order).get("E6")).toBe(2);
  });
});

describe("groupCitationsByDocument", () => {
  const sameDoc: Record<string, CitationMeta> = {
    E5: { evidence_id: "E5", title: "Device Controller", page: 3 },
    E6: { evidence_id: "E6", title: "Device Controller", page: 3 },
    E7: { evidence_id: "E7", title: "Device Controller", page: 5 },
    E10: { evidence_id: "E10", title: "Device Controller", page: 12 },
  };

  it("gives every chunk from the same document one citation number", () => {
    const sentences: ChatSentence[] = [
      { text: "A [E5].", evidence: ["E5"], support: "supported" },
      { text: "B [E6].", evidence: ["E6"], support: "supported" },
      { text: "C [E7].", evidence: ["E7"], support: "partial" },
      { text: "D [E10].", evidence: ["E10"], support: "supported" },
    ];
    const { groups, indexByEvidence } = groupCitationsByDocument(sentences, sameDoc);
    expect(groups).toHaveLength(1);
    expect(groups[0]?.number).toBe(1);
    expect(groups[0]?.title).toBe("Device Controller");
    expect(indexByEvidence.get("E5")).toBe(1);
    expect(indexByEvidence.get("E6")).toBe(1);
    expect(indexByEvidence.get("E7")).toBe(1);
    expect(indexByEvidence.get("E10")).toBe(1);
  });

  it("lists distinct pages once instead of repeating the document", () => {
    const sentences: ChatSentence[] = [
      { text: "A [E5].", evidence: ["E5"], support: "supported" },
      { text: "B [E6].", evidence: ["E6"], support: "supported" },
      { text: "C [E7].", evidence: ["E7"], support: "partial" },
      { text: "D [E10].", evidence: ["E10"], support: "supported" },
    ];
    const { groups } = groupCitationsByDocument(sentences, sameDoc);
    expect(groups[0]?.pages.map((p) => p.page)).toEqual([3, 5, 12]);
    expect(groups[0]?.pages.find((p) => p.page === 3)?.evidenceId).toBe("E5");
    expect(groups[0]?.pages.find((p) => p.page === 5)?.evidenceId).toBe("E7");
  });

  it("numbers a second document separately", () => {
    const sentences: ChatSentence[] = [
      { text: "A [E5].", evidence: ["E5"], support: "supported" },
      { text: "B [E9].", evidence: ["E9"], support: "supported" },
    ];
    const citations: Record<string, CitationMeta> = {
      E5: { evidence_id: "E5", title: "Device Controller", page: 3 },
      E9: { evidence_id: "E9", title: "Survey Guide", page: 1 },
    };
    const { groups, indexByEvidence } = groupCitationsByDocument(sentences, citations);
    expect(groups.map((g) => g.title)).toEqual(["Device Controller", "Survey Guide"]);
    expect(indexByEvidence.get("E5")).toBe(1);
    expect(indexByEvidence.get("E9")).toBe(2);
  });

  it("looks up metadata when the payload is keyed by C-ids", () => {
    const sentences: ChatSentence[] = [
      { text: "A [E5].", evidence: ["E5"], support: "supported" },
      { text: "B [E6].", evidence: ["E6"], support: "supported" },
    ];
    const citations: Record<string, CitationMeta> = {
      C1: { evidence_id: "E5", title: "Device Controller", page: 3 },
      C2: { evidence_id: "E6", title: "Device Controller", page: 5 },
    };
    const { groups, indexByEvidence } = groupCitationsByDocument(sentences, citations);
    expect(groups).toHaveLength(1);
    expect(indexByEvidence.get("E5")).toBe(1);
    expect(indexByEvidence.get("E6")).toBe(1);
  });
});

describe("uniqueSourcesForSentence", () => {
  it("keeps one chip per document even when several evidence ids are cited", () => {
    const indexByEvidence = new Map([
      ["E5", 1],
      ["E6", 1],
      ["E9", 2],
    ]);
    expect(uniqueSourcesForSentence(["E5", "E6", "E9"], indexByEvidence)).toEqual([
      "E5",
      "E9",
    ]);
  });
});

describe("lookupCitation", () => {
  it("finds metadata by evidence_id when the record uses a different key", () => {
    const citations: Record<string, CitationMeta> = {
      C1: { evidence_id: "E5", title: "Device Controller", page: 3 },
    };
    expect(lookupCitation("E5", citations)?.title).toBe("Device Controller");
  });
});

describe("groupSentences", () => {
  it("keeps short answers in one paragraph", () => {
    const sentences: ChatSentence[] = [
      { text: "A.", evidence: [], support: "supported" },
      { text: "B.", evidence: [], support: "supported" },
    ];
    expect(groupSentences(sentences)).toHaveLength(1);
  });
});
