/**
 * @file EvidenceInspector.tsx
 * @description Persistent evidence panel for the chat page: one card per cited source
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-26
 * @modified 2026-09-26
 * @version 0.1.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 * with its actual retrieved passage, section/page, extraction method and relevance —
 * not just a title, so grounding is verifiable at a glance rather than one click away.
 */

import { FileText, ScanLine, ShieldCheck, Sparkles } from "lucide-react";
import { dedupeCitations, type CitationMeta } from "@/lib/chat-answer";
import { cn } from "@/lib/utils";

const METHOD_ICON: Record<string, typeof FileText> = {
  digital: FileText,
  ocr: ScanLine,
  vision: Sparkles,
};

function EvidenceCard({
  meta,
  text,
  active,
  onSelect,
}: {
  meta: CitationMeta;
  text: string;
  active: boolean;
  onSelect: () => void;
}) {
  const Icon = METHOD_ICON[meta.extraction_method ?? "digital"] ?? FileText;
  const relevancePct = Math.round(Math.max(0, Math.min(1, meta.relevance ?? 1)) * 100);

  return (
    <button
      type="button"
      data-testid={`evidence-card-${meta.evidence_id.toLowerCase()}`}
      onClick={onSelect}
      className={cn(
        "w-full space-y-2 rounded-md border bg-card p-3 text-left transition-colors",
        active ? "border-cited shadow-[0_0_0_1px_hsl(var(--cited))]" : "border-border hover:border-cited/50",
      )}
    >
      <div className="flex items-center gap-2">
        <span className="rounded-sm bg-cited/10 px-1.5 py-0.5 font-mono text-[11px] font-semibold text-cited">
          {meta.evidence_id}
        </span>
        <span className="min-w-0 flex-1 truncate text-sm font-medium text-foreground" title={meta.title}>
          {meta.title}
        </span>
      </div>
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1 font-mono text-[11px] text-muted-foreground">
        {meta.section ? <span className="truncate">§ {meta.section}</span> : null}
        {meta.page != null ? <span>p.{meta.page}</span> : null}
        <span className="flex items-center gap-1">
          <Icon className="h-3 w-3" aria-hidden="true" /> {meta.extraction_method ?? "digital"}
        </span>
      </div>
      <p className="line-clamp-5 text-[13px] leading-relaxed text-foreground/90">{text}</p>
      <div className="flex items-center gap-2">
        <span className="font-mono text-[10px] uppercase tracking-wide text-muted-foreground">relevance</span>
        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
          <div className="h-full rounded-full bg-cited" style={{ width: `${relevancePct}%` }} />
        </div>
        <span className="font-mono text-[10px] text-muted-foreground">{relevancePct}%</span>
      </div>
    </button>
  );
}

export function EvidenceInspector({
  citations,
  evidenceText,
  activeId,
  onSelect,
}: {
  citations: Record<string, CitationMeta>;
  evidenceText: Record<string, string>;
  activeId: string | null;
  onSelect: (evidenceId: string) => void;
}) {
  const sources = dedupeCitations(citations);

  if (sources.length === 0) {
    return (
      <div
        data-testid="evidence-inspector"
        className="flex h-full flex-col items-center justify-center gap-2 p-6 text-center text-sm text-muted-foreground"
      >
        <ShieldCheck className="h-6 w-6 opacity-50" aria-hidden="true" />
        <p>Ask a question. The passages behind the answer will appear here, with the exact
          text that was retrieved, not a paraphrase.</p>
      </div>
    );
  }

  return (
    <div data-testid="evidence-inspector" className="flex h-full flex-col">
      <div className="border-b border-border px-3 py-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        Sources ({sources.length})
      </div>
      <div className="flex-1 space-y-2 overflow-y-auto p-3">
        {sources.map((meta) => (
          <EvidenceCard
            key={meta.evidence_id}
            meta={meta}
            text={meta.text || evidenceText[meta.evidence_id] || meta.title}
            active={activeId === meta.evidence_id}
            onSelect={() => onSelect(meta.evidence_id)}
          />
        ))}
      </div>
    </div>
  );
}
