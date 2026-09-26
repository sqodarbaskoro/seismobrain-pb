/**
 * @file chat-answer.ts
 * @description Helpers to render grounded chat answers as readable prose
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.2.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

export type Support = "supported" | "partial" | "unsupported" | "no_citation" | string;

export type ChatSentence = {
  text: string;
  evidence: string[];
  support: Support;
};

export type CitationMeta = {
  evidence_id: string;
  title: string;
  section?: string;
  page?: number | null;
  extraction_method?: string;
  /** The actual cited passage, as retrieved — not the LLM's paraphrase. */
  text?: string;
  /** Retrieval relevance in [0, 1], highest-ranked source = 1.0. */
  relevance?: number;
};

export type SourcePage = {
  page: number;
  evidenceId: string;
};

export type SourceGroup = {
  number: number;
  title: string;
  evidenceId: string;
  pages: SourcePage[];
};

/** Model-emitted evidence tags such as [E5] or [E2][E5]. */
const EVIDENCE_TAG = /\s*\[E\d+\]/gi;

/** Remove server/LLM evidence tags so the reader sees prose, not markers. */
export function stripEvidenceTags(text: string): string {
  return text.replace(EVIDENCE_TAG, "").replace(/[ \t]{2,}/g, " ").trim();
}

/** Unique evidence IDs in the order they first appear in the answer. */
export function citationOrder(sentences: ChatSentence[]): string[] {
  const seen = new Set<string>();
  const order: string[] = [];
  for (const sentence of sentences) {
    for (const eid of sentence.evidence) {
      if (!seen.has(eid)) {
        seen.add(eid);
        order.push(eid);
      }
    }
  }
  return order;
}

/** 1-based citation numbers for inline superscripts and the sources list. */
export function citationIndexMap(order: string[]): Map<string, number> {
  return new Map(order.map((eid, index) => [eid, index + 1]));
}

/** Resolve citation metadata whether the payload is keyed by E-id or C-id. */
export function lookupCitation(
  eid: string,
  citations: Record<string, CitationMeta>,
): CitationMeta | undefined {
  const direct = citations[eid];
  if (direct) return direct;
  return Object.values(citations).find((meta) => meta.evidence_id === eid);
}

function documentKey(eid: string, citations: Record<string, CitationMeta>): string {
  const title = lookupCitation(eid, citations)?.title?.trim();
  return title ? title.toLowerCase() : eid;
}

/**
 * Number sources by document, not by evidence chunk. Same file → one number;
 * distinct pages are collected so the sources list can show them without repeating
 * the title.
 */
export function groupCitationsByDocument(
  sentences: ChatSentence[],
  citations: Record<string, CitationMeta>,
): { groups: SourceGroup[]; indexByEvidence: Map<string, number> } {
  const groups: SourceGroup[] = [];
  const keyToIndex = new Map<string, number>();
  const indexByEvidence = new Map<string, number>();

  for (const sentence of sentences) {
    for (const eid of sentence.evidence) {
      const key = documentKey(eid, citations);
      let groupIndex = keyToIndex.get(key);
      if (groupIndex === undefined) {
        const meta = lookupCitation(eid, citations);
        groupIndex = groups.length;
        keyToIndex.set(key, groupIndex);
        groups.push({
          number: groupIndex + 1,
          title: meta?.title?.trim() || eid,
          evidenceId: eid,
          pages: [],
        });
      }
      const group = groups[groupIndex];
      const page = lookupCitation(eid, citations)?.page;
      if (typeof page === "number" && !group.pages.some((entry) => entry.page === page)) {
        group.pages.push({ page, evidenceId: eid });
        group.pages.sort((a, b) => a.page - b.page);
      }
      indexByEvidence.set(eid, group.number);
    }
  }

  return { groups, indexByEvidence };
}

/** First evidence id per source number so a sentence does not repeat the same chip. */
export function uniqueSourcesForSentence(
  evidence: string[],
  indexByEvidence: Map<string, number>,
): string[] {
  const seen = new Set<number>();
  const out: string[] = [];
  for (const eid of evidence) {
    const n = indexByEvidence.get(eid);
    if (n == null || seen.has(n)) continue;
    seen.add(n);
    out.push(eid);
  }
  return out;
}

/** Split a long answer into short paragraphs so it stays scannable. */
export function groupSentences(sentences: ChatSentence[], size = 3): ChatSentence[][] {
  if (sentences.length === 0) return [];
  const groups: ChatSentence[][] = [];
  for (let i = 0; i < sentences.length; i += size) {
    groups.push(sentences.slice(i, i + size));
  }
  return groups;
}

export function isFullySupported(support: Support): boolean {
  return support === "supported";
}

/**
 * Unique citations by underlying evidence chunk, in first-seen order. A single
 * evidence id can be assigned more than one C-id when it backs sentences in
 * different parts of the answer; the inspector shows one card per source, not
 * one per mention.
 */
export function dedupeCitations(citations: Record<string, CitationMeta>): CitationMeta[] {
  const seen = new Set<string>();
  const out: CitationMeta[] = [];
  for (const meta of Object.values(citations)) {
    if (seen.has(meta.evidence_id)) continue;
    seen.add(meta.evidence_id);
    out.push(meta);
  }
  return out;
}
