/**
 * @file ChatAnswer.tsx
 * @description Flowing grounded-chat answer: prose, inline citations, sources
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.2.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import {
  groupCitationsByDocument,
  groupSentences,
  isFullySupported,
  lookupCitation,
  stripEvidenceTags,
  uniqueSourcesForSentence,
  type ChatSentence,
  type CitationMeta,
  type SourceGroup,
} from "@/lib/chat-answer";
import { sanitizeMarkdown } from "@/lib/markdown";
import { cn } from "@/lib/utils";

export type { CitationMeta };

function sourceLabel(
  eid: string,
  citations: Record<string, CitationMeta>,
  evidenceText: Record<string, string>,
): string {
  const meta = lookupCitation(eid, citations);
  if (meta?.title) {
    const parts = [meta.title];
    if (meta.page != null) parts.push(`p.${meta.page}`);
    return parts.join(" · ");
  }
  return evidenceText[eid] || eid;
}

function groupLabel(group: SourceGroup): string {
  if (group.pages.length === 1) {
    return `${group.title} · p.${group.pages[0].page}`;
  }
  return group.title;
}

export function ChatAnswer({
  sentences,
  citations,
  evidenceText,
  onCite,
}: {
  sentences: ChatSentence[];
  citations: Record<string, CitationMeta>;
  evidenceText: Record<string, string>;
  onCite: (evidenceId: string) => void;
}) {
  const { groups, indexByEvidence } = groupCitationsByDocument(sentences, citations);
  const paragraphs = groupSentences(sentences);
  const flagged = sentences.filter((s) => !isFullySupported(s.support)).length;

  return (
    <article
      data-testid="assistant-answer"
      className="max-w-prose rounded-2xl border border-border bg-card px-5 py-4 shadow-sm"
    >
      <div className="space-y-4">
        {paragraphs.map((group, paragraphIndex) => (
          <p
            key={paragraphIndex}
            className="text-[15px] leading-relaxed text-foreground"
          >
            {group.map((sentence, sentenceIndex) => {
              const body = stripEvidenceTags(sanitizeMarkdown(sentence.text));
              const flaggedSentence = !isFullySupported(sentence.support);
              const chips = uniqueSourcesForSentence(sentence.evidence, indexByEvidence);
              return (
                <span
                  key={`${paragraphIndex}-${sentenceIndex}`}
                  className={cn(
                    flaggedSentence &&
                      "underline decoration-dotted decoration-warning/70 underline-offset-4",
                  )}
                  title={flaggedSentence ? sentence.support : undefined}
                >
                  {body}
                  {chips.map((eid) => {
                    const n = indexByEvidence.get(eid) ?? 0;
                    const meta = lookupCitation(eid, citations);
                    return (
                      <button
                        key={eid}
                        type="button"
                        data-testid="citation-chip"
                        className="ml-0.5 inline-flex h-4 min-w-4 shrink-0 items-center justify-center whitespace-nowrap rounded-sm bg-cited/10 px-1 align-super font-mono text-[10px] font-semibold leading-none text-cited hover:bg-cited/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                        aria-label={`Open source ${n}: ${sourceLabel(eid, citations, evidenceText)}`}
                        title={
                          meta?.page != null
                            ? `${meta.title || "Source"} · p.${meta.page}`
                            : meta?.title
                        }
                        onClick={() => onCite(eid)}
                      >
                        {n}
                      </button>
                    );
                  })}
                  <span data-testid="support-badge" className="sr-only">
                    {sentence.support}
                  </span>
                  {sentenceIndex < group.length - 1 ? " " : null}
                </span>
              );
            })}
          </p>
        ))}
      </div>

      {flagged > 0 ? (
        <p className="mt-3 text-xs text-warning" data-testid="grounding-note">
          {flagged === 1
            ? "One claim is only partly supported by the sources."
            : `${flagged} claims are only partly supported by the sources.`}
        </p>
      ) : null}

      {groups.length > 0 ? (
        <footer className="mt-4 border-t border-border pt-3" data-testid="answer-sources">
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Sources
          </h2>
          <ol className="space-y-2">
            {groups.map((source) => (
              <li key={source.number} data-testid="answer-source">
                <div className="flex items-start gap-2">
                  <span className="mt-0.5 w-4 shrink-0 font-mono text-xs font-semibold text-cited">
                    {source.number}
                  </span>
                  <div className="min-w-0 flex-1">
                    <button
                      type="button"
                      className="rounded-md text-left text-sm text-foreground/80 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      onClick={() => onCite(source.evidenceId)}
                    >
                      {groupLabel(source)}
                    </button>
                    {source.pages.length > 1 ? (
                      <div className="mt-1 flex flex-wrap gap-1" data-testid="source-pages">
                        {source.pages.map((entry) => (
                          <button
                            key={entry.page}
                            type="button"
                            data-testid="source-page"
                            className="inline-flex items-center rounded-md bg-cited/10 px-1.5 py-0.5 font-mono text-[11px] font-medium text-cited hover:bg-cited/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                            aria-label={`Open ${source.title} page ${entry.page}`}
                            onClick={() => onCite(entry.evidenceId)}
                          >
                            p.{entry.page}
                          </button>
                        ))}
                      </div>
                    ) : null}
                  </div>
                </div>
              </li>
            ))}
          </ol>
        </footer>
      ) : null}
    </article>
  );
}
