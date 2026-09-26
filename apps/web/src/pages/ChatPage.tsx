/**
 * @file ChatPage.tsx
 * @description Chat shell wired to conversations SSE API (FR-CHAT)
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-16
 * @modified 2026-09-18
 * @version 0.11.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { AlertTriangle, Layers, Sparkles, ThumbsDown, ThumbsUp, Trash2 } from "lucide-react";
import { ApiError, apiFetch, apiJson } from "@/api/client";
import { getAccessToken } from "@/auth/session";
import { listMyWorkspaces, type MyWorkspace } from "@/api/services/workspaces";
import { ChatAnswer } from "@/components/ChatAnswer";
import { ChatThinking } from "@/components/ChatThinking";
import { EvidenceInspector } from "@/components/EvidenceInspector";
import { Button } from "@/components/ui/button";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { dedupeCitations, type ChatSentence, type CitationMeta } from "@/lib/chat-answer";
import { restoreHistory, type ConversationHistory, type Turn } from "@/lib/chat-history";
import { useTheme } from "@/lib/theme";

type Conversation = { id: string; title: string };

function ChatEmptyState() {
  return (
    <div className="mx-auto max-w-md space-y-4 pt-8 text-center">
      <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-cited/10">
        <Sparkles className="h-5 w-5 text-cited" aria-hidden="true" />
      </div>
      <div>
        <p className="text-sm font-medium text-foreground">Ask a question about your documents.</p>
        <p className="mt-1 text-xs text-muted-foreground">
          Every claim is backed by a citation you can inspect, or the system says so.
        </p>
      </div>
    </div>
  );
}

const REFUSAL_HINTS: Record<string, string> = {
  no_evidence: "Nothing in the current scope addresses this. Try widening the collection scope or uploading the relevant document.",
  insufficient_evidence: "The retrieved evidence doesn't fully support an answer. Try rephrasing the question or narrowing it.",
  unsupported: "The system could not verify a grounded answer for this question.",
};

function RefusalCallout({ type, message }: { type: string; message: string }) {
  return (
    <div
      data-testid="refusal-callout"
      className="max-w-[85%] space-y-2 rounded-md border border-destructive/40 bg-destructive/10 px-4 py-3"
    >
      <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-destructive">
        <AlertTriangle className="h-4 w-4" aria-hidden="true" /> {type}
      </div>
      <p className="text-sm text-foreground">{message}</p>
      <p className="text-xs text-muted-foreground">
        {REFUSAL_HINTS[type] ?? REFUSAL_HINTS.unsupported}
      </p>
    </div>
  );
}

function FeedbackButtons({
  messageId,
  feedback,
  onVote,
}: {
  messageId: string;
  feedback: "up" | "down" | null;
  onVote: (messageId: string, rating: "up" | "down") => void;
}) {
  return (
    <div className="mt-2 flex items-center gap-1 border-t border-border pt-2">
      <span className="text-[11px] text-muted-foreground">Was this answer helpful?</span>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className={cn("h-7 w-7", feedback === "up" ? "text-success" : "text-muted-foreground")}
        aria-label="Good answer"
        aria-pressed={feedback === "up"}
        onClick={() => onVote(messageId, "up")}
      >
        <ThumbsUp className="h-3.5 w-3.5" aria-hidden="true" />
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className={cn("h-7 w-7", feedback === "down" ? "text-destructive" : "text-muted-foreground")}
        aria-label="Bad answer"
        aria-pressed={feedback === "down"}
        onClick={() => onVote(messageId, "down")}
      >
        <ThumbsDown className="h-3.5 w-3.5" aria-hidden="true" />
      </Button>
    </div>
  );
}

export function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();
  const [initialConversationId] = useState(() => searchParams.get("conversation"));
  // Guided setup's last step links here with a suggested first question pre-filled.
  const [input, setInput] = useState(() => searchParams.get("q") ?? "");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [responding, setResponding] = useState(false);
  const [loading, setLoading] = useState(true);
  const [viewerOpen, setViewerOpen] = useState(false);
  const [viewerTurn, setViewerTurn] = useState(0);
  const [viewerEvidence, setViewerEvidence] = useState<string | null>(null);
  const { theme } = useTheme();
  const [whyOpen, setWhyOpen] = useState(false);
  const [convListOpen, setConvListOpen] = useState(false);
  const [locality, setLocality] = useState<"local" | "external">("external");
  const [lastMessageId, setLastMessageId] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Conversation | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [stage, setStage] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<Record<string, "up" | "down">>({});
  const composerRef = useRef<HTMLTextAreaElement | null>(null);

  // Auto-grow the composer with its content instead of scrolling a single line, up to a
  // cap (CSS max-h) beyond which it scrolls internally.
  useEffect(() => {
    const el = composerRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, [input]);

  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<string | null>(null);
  const [selectedCollectionIds, setSelectedCollectionIds] = useState<string[]>([]);
  const [scopePickerOpen, setScopePickerOpen] = useState(false);

  const workspacesQuery = useQuery({
    queryKey: ["my-workspaces"],
    queryFn: () => listMyWorkspaces(),
  });
  const workspaces = workspacesQuery.data?.workspaces ?? [];
  const activeWorkspace = workspaces.find((w) => w.id === selectedWorkspaceId) ?? null;
  const availableCollections = activeWorkspace?.collections ?? [];

  // Default to the first workspace (and all of its collections in scope) once the
  // list loads, or if the previously selected one disappears (e.g. access revoked).
  useEffect(() => {
    if (workspaces.length === 0) return;
    if (selectedWorkspaceId && workspaces.some((w) => w.id === selectedWorkspaceId)) return;
    const first = workspaces[0];
    setSelectedWorkspaceId(first.id);
    setSelectedCollectionIds(first.collections.map((c) => c.id));
  }, [workspaces, selectedWorkspaceId]);

  function switchWorkspace(workspace: MyWorkspace) {
    setSelectedWorkspaceId(workspace.id);
    setSelectedCollectionIds(workspace.collections.map((c) => c.id));
  }

  function toggleCollection(id: string) {
    setSelectedCollectionIds((prev) =>
      prev.includes(id) ? prev.filter((c) => c !== id) : [...prev, id],
    );
  }

  const providersQuery = useQuery({
    queryKey: ["providers"],
    queryFn: () =>
      apiJson<{ providers: { locality: string }[] }>("/admin/providers").catch(() => ({
        providers: [],
      })),
  });

  useEffect(() => {
    const first = providersQuery.data?.providers[0];
    if (first?.locality === "local") setLocality("local");
    else if (first) setLocality("external");
  }, [providersQuery.data]);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const listed = await apiJson<{ conversations: Conversation[] }>(
          "/api/v1/conversations",
        );
        if (cancelled) return;
        setConversations(listed.conversations);
        const selected = listed.conversations.find((c) => c.id === initialConversationId)
          ?? listed.conversations[0];
        if (selected) {
          const history = await apiJson<ConversationHistory>(
            `/api/v1/conversations/${selected.id}/messages`,
          );
          if (cancelled) return;
          const restored = restoreHistory(history);
          setActiveId(selected.id);
          setTurns(restored.turns);
          setLastMessageId(restored.lastMessageId);
          setViewerTurn(Math.max(0, restored.turns.length - 1));
          setViewerEvidence(null);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof ApiError ? err.detail : "Failed to load conversations");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [initialConversationId]);

  function activateConversation(id: string | null) {
    setActiveId(id);
    setSearchParams((params) => {
      if (id) params.set("conversation", id);
      else params.delete("conversation");
      return params;
    }, { replace: true });
    setViewerOpen(false);
    setConvListOpen(false);
  }

  async function selectConversation(id: string) {
    if (busy || loading || id === activeId) return;
    setLoading(true);
    setError(null);
    try {
      const history = await apiJson<ConversationHistory>(`/api/v1/conversations/${id}/messages`);
      const restored = restoreHistory(history);
      setTurns(restored.turns);
      setLastMessageId(restored.lastMessageId);
      setViewerTurn(Math.max(0, restored.turns.length - 1));
      setViewerEvidence(null);
      setInput("");
      activateConversation(id);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to load conversation");
    } finally {
      setLoading(false);
    }
  }

  async function ensureConversation(): Promise<string> {
    if (activeId) return activeId;
    const created = await apiJson<Conversation>("/api/v1/conversations", {
      method: "POST",
      body: JSON.stringify({ title: "New chat", workspace_id: selectedWorkspaceId ?? "default" }),
    });
    setConversations((prev) => [created, ...prev]);
    activateConversation(created.id);
    return created.id;
  }

  async function send() {
    const q = input.trim();
    if (!q || busy || loading) return;
    setError(null);
    setBusy(true);
    setResponding(true);
    setInput("");
    const turnIndex = turns.length;
    setTurns((prev) => [
      ...prev,
      {
        question: q,
        sentences: [],
        citations: {},
        evidenceText: {},
        refusalType: null,
        messageId: null,
        trace: null,
      },
    ]);
    setViewerTurn(turnIndex);
    setViewerEvidence(null);
    setStage(null);
    const updateLastTurn = (patch: Partial<Turn>) => {
      setTurns((prev) => {
        const next = [...prev];
        const last = next[next.length - 1];
        if (last) next[next.length - 1] = { ...last, ...patch };
        return next;
      });
    };
    try {
      const convId = await ensureConversation();
      const token = getAccessToken();
      const res = await apiFetch(`/api/v1/conversations/${convId}/messages`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        body: JSON.stringify({
          content: q,
          scope: { collections: selectedCollectionIds },
        }),
      });
      if (!res.ok || !res.body) {
        throw new ApiError(res.status, await res.text());
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      const nextSentences: ChatSentence[] = [];
      const nextCitations: Record<string, CitationMeta> = {};
      const nextEvidence: Record<string, string> = {};
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";
        for (const block of parts) {
          let event = "message";
          let data = "";
          for (const line of block.split("\n")) {
            if (line.startsWith("event: ")) event = line.slice(7);
            if (line.startsWith("data: ")) data = line.slice(6);
          }
          if (!data) continue;
          const payload = JSON.parse(data) as Record<string, unknown>;
          if (event === "conversation" && typeof payload.title === "string") {
            const title = payload.title;
            setConversations((prev) => prev.map((c) => c.id === convId ? { ...c, title } : c));
          }
          if (event === "status" && typeof payload.stage === "string") {
            setStage(payload.stage);
          }
          if (event === "trace") {
            updateLastTurn({
              trace: {
                resolvedQuery: String(payload.resolved_query || q),
                route: String(payload.route || ""),
                collectionIds: Array.isArray(payload.collection_ids)
                  ? (payload.collection_ids as string[])
                  : null,
                evidenceCount: typeof payload.evidence_count === "number" ? payload.evidence_count : 0,
                latencyMs: typeof payload.latency_ms === "number" ? payload.latency_ms : 0,
              },
            });
          }
          if (event === "sentence") {
            nextSentences.push({
              text: String(payload.text || ""),
              evidence: (payload.evidence as string[]) || [],
              support: String(payload.support || "supported"),
            });
            updateLastTurn({ sentences: [...nextSentences] });
          }
          if (event === "evidence") {
            const items = (payload.items as Array<Record<string, unknown>>) || [];
            for (const item of items) {
              const label = String(item.label || "");
              const title = String(item.title || "");
              const section = String(item.section_path || "");
              const text = typeof item.text === "string" ? item.text : "";
              nextEvidence[label] = text || `${title} ${section}`.trim();
              nextCitations[label] = {
                evidence_id: label,
                title,
                section,
                page: typeof item.page === "number" ? item.page : null,
                extraction_method: String(item.extraction_method || ""),
                text: text || undefined,
                relevance: typeof item.score === "number" ? item.score : undefined,
              };
            }
            updateLastTurn({ evidenceText: { ...nextEvidence }, citations: { ...nextCitations } });
            const firstLabel = items.length > 0 ? String(items[0].label || "") || null : null;
            setViewerEvidence((cur) => cur ?? firstLabel);
          }
          if (event === "refusal") {
            const refusal = payload.refusal as { message?: string; type?: string } | undefined;
            nextSentences.push({
              text: refusal?.message || "Unable to answer",
              evidence: [],
              support: refusal?.type || "unsupported",
            });
            updateLastTurn({ sentences: [...nextSentences], refusalType: refusal?.type || "unsupported" });
          }
          if (event === "final") {
            const messageId = String(payload.id || "");
            setLastMessageId(messageId);
            if (typeof payload.conversation_title === "string") {
              const title = payload.conversation_title;
              setConversations((prev) => prev.map((c) => c.id === convId ? { ...c, title } : c));
            }
            const cites = (payload.citations || {}) as Record<string, CitationMeta>;
            for (const meta of Object.values(cites)) {
              const id = meta.evidence_id;
              if (!id) continue;
              nextCitations[id] = { ...nextCitations[id], ...meta, evidence_id: id };
            }
            updateLastTurn({ citations: { ...nextCitations }, messageId });
          }
        }
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Send failed");
    } finally {
      setBusy(false);
      setResponding(false);
      setStage(null);
    }
  }

  async function vote(messageId: string, rating: "up" | "down") {
    const previous = feedback[messageId] ?? null;
    setFeedback((prev) => ({ ...prev, [messageId]: rating }));
    try {
      await apiJson("/api/v1/feedback", {
        method: "POST",
        body: JSON.stringify({ message_id: messageId, rating, reason: `thumbs_${rating}` }),
      });
    } catch {
      setFeedback((prev) => {
        const next = { ...prev };
        if (previous) next[messageId] = previous;
        else delete next[messageId];
        return next;
      });
    }
  }

  async function onNewChat() {
    if (busy || loading) return;
    setBusy(true);
    setError(null);
    try {
      const created = await apiJson<Conversation>("/api/v1/conversations", {
        method: "POST",
        body: JSON.stringify({ title: "New chat", workspace_id: selectedWorkspaceId ?? "default" }),
      });
      setConversations((prev) => [created, ...prev]);
      activateConversation(created.id);
      setTurns([]);
      setInput("");
      setLastMessageId(null);
      setViewerTurn(0);
      setViewerEvidence(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not create conversation");
    } finally {
      setBusy(false);
    }
  }

  async function onDeleteChat() {
    if (!deleteTarget || busy || loading) return;
    setBusy(true);
    setDeleteError(null);
    try {
      await apiJson(`/api/v1/conversations/${deleteTarget.id}`, { method: "DELETE" });
      setConversations((prev) => prev.filter((c) => c.id !== deleteTarget.id));
      if (activeId === deleteTarget.id) {
        activateConversation(null);
        setTurns([]);
        setLastMessageId(null);
        setInput("");
        setError(null);
        setViewerTurn(0);
        setViewerEvidence(null);
      }
      setDeleteTarget(null);
    } catch (err) {
      setDeleteError(err instanceof ApiError ? err.detail : "Could not delete conversation");
    } finally {
      setBusy(false);
    }
  }

  async function onCopy() {
    if (!activeId || !lastMessageId) return;
    const copied = await apiJson<{ markdown: string }>(
      `/api/v1/conversations/${activeId}/messages/${lastMessageId}/copy`,
    );
    await navigator.clipboard.writeText(copied.markdown);
  }

  const lastTurn = turns[turns.length - 1];
  const focusTurn = turns[viewerTurn];
  const focusCitations = focusTurn?.citations ?? {};
  const focusEvidenceText = focusTurn?.evidenceText ?? {};
  const sourceCount = new Set(Object.values(focusCitations).map((c) => c.evidence_id)).size;

  return (
    <div className={cn("bg-background text-foreground", theme === "dark" && "dark")} data-testid="chat-page">
      <div className="mx-auto grid min-h-[calc(100vh-3.5rem)] max-w-6xl grid-cols-1 gap-0 md:grid-cols-[240px_1fr] lg:grid-cols-[240px_1fr_320px]">
        <aside
          id="conversation-panel"
          className={`border-r border-border p-4 md:block ${convListOpen ? "block" : "hidden"}`}
          aria-label="Conversation list"
        >
          <h1 className="mb-4 text-lg font-semibold tracking-tight">Chats</h1>
          <button
            type="button"
            data-testid="new-chat-button"
            className="mb-3 text-sm underline"
            onClick={() => void onNewChat()}
            disabled={busy || loading}
          >
            New chat
          </button>
          <ul data-testid="conversation-list" className="space-y-2">
            {conversations.map((c) => (
              <li key={c.id} className="flex min-w-0 items-center gap-1">
                <button
                  type="button"
                  className={`min-w-0 flex-1 truncate rounded px-2 py-2 text-left text-sm ${
                    c.id === activeId ? "border border-primary/30 bg-primary/10 font-medium" : ""
                  }`}
                  onClick={() => void selectConversation(c.id)}
                  disabled={busy || loading}
                  aria-current={c.id === activeId ? "true" : undefined}
                  title={c.title}
                >
                  {c.title}
                </button>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="shrink-0 text-muted-foreground hover:text-destructive"
                  aria-label={`Delete chat: ${c.title}`}
                  title="Delete chat"
                  disabled={busy || loading}
                  onClick={() => {
                    setDeleteError(null);
                    setDeleteTarget(c);
                  }}
                >
                  <Trash2 aria-hidden="true" />
                </Button>
              </li>
            ))}
          </ul>
        </aside>

        <section className="flex flex-col" aria-label="Active thread">
          <div className="border-b border-border px-4 py-2 md:hidden">
            <button
              type="button"
              className="text-sm underline"
              aria-expanded={convListOpen}
              aria-controls="conversation-panel"
              onClick={() => setConvListOpen((open) => !open)}
            >
              {convListOpen ? "Hide chats" : "Chats"}
            </button>
          </div>
          <div
            className="flex flex-wrap items-center gap-2 border-b border-border px-4 py-2 text-sm"
            data-testid="scope-bar"
            aria-label="Active collections and filters"
          >
            {workspaces.length > 0 ? (
              <Select
                value={selectedWorkspaceId ?? undefined}
                onValueChange={(id) => {
                  const workspace = workspaces.find((w) => w.id === id);
                  if (workspace) switchWorkspace(workspace);
                }}
              >
                <SelectTrigger
                  data-testid="workspace-select"
                  aria-label="Workspace"
                  className="h-7 w-auto min-w-0 gap-1.5 border-none bg-transparent px-1.5 py-0 text-sm font-medium shadow-none focus:ring-0"
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {workspaces.map((w) => (
                    <SelectItem key={w.id} value={w.id}>
                      {w.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <span className="font-medium">Scope:</span>
            )}
            <button
              type="button"
              data-testid="scope-picker-toggle"
              aria-expanded={scopePickerOpen}
              aria-controls="scope-picker-panel"
              className="flex items-center gap-1.5 rounded border border-border px-2 py-0.5 text-xs hover:border-cited/50 disabled:opacity-50"
              onClick={() => setScopePickerOpen((o) => !o)}
              disabled={availableCollections.length === 0}
            >
              <Layers className="h-3 w-3" aria-hidden="true" />
              {availableCollections.length === 0
                ? "No collections"
                : `${selectedCollectionIds.length}/${availableCollections.length} collections`}
            </button>
            <span
              data-testid="provider-badge"
              className="ml-auto rounded border border-success px-2 py-0.5 font-mono text-xs uppercase tracking-wide text-success"
            >
              {locality === "local" ? "Processed locally" : "External provider"}
            </span>
            <button
              type="button"
              className="text-xs underline"
              data-testid="why-answer-toggle"
              onClick={() => setWhyOpen((o) => !o)}
            >
              Why this answer
            </button>
            {lastMessageId ? (
              <button type="button" className="text-xs underline" onClick={() => void onCopy()}>
                Copy
              </button>
            ) : null}
            <button
              type="button"
              className="rounded border border-border px-2 py-0.5 text-xs lg:hidden"
              data-testid="mobile-evidence-button"
              onClick={() => setViewerOpen(true)}
            >
              Sources ({sourceCount})
            </button>
          </div>

          {scopePickerOpen ? (
            <div
              id="scope-picker-panel"
              data-testid="scope-picker-panel"
              className="border-b border-border bg-muted px-4 py-3 text-sm"
            >
              {availableCollections.length === 0 ? (
                <p className="text-xs text-muted-foreground">
                  No collections in this workspace yet.
                </p>
              ) : (
                <>
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Collections in scope
                    </span>
                    <div className="flex gap-2 text-xs">
                      <button
                        type="button"
                        className="underline"
                        onClick={() => setSelectedCollectionIds(availableCollections.map((c) => c.id))}
                      >
                        All
                      </button>
                      <button
                        type="button"
                        className="underline"
                        onClick={() => setSelectedCollectionIds([])}
                      >
                        None
                      </button>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-x-4 gap-y-1.5">
                    {availableCollections.map((c) => (
                      <label key={c.id} className="flex items-center gap-1.5 text-sm">
                        <input
                          type="checkbox"
                          data-testid={`scope-collection-${c.id}`}
                          checked={selectedCollectionIds.includes(c.id)}
                          onChange={() => toggleCollection(c.id)}
                        />
                        {c.name}
                      </label>
                    ))}
                  </div>
                </>
              )}
            </div>
          ) : null}

          {whyOpen ? (
            <aside
              data-testid="why-this-answer"
              className="border-b border-border bg-muted px-4 py-3 text-sm"
              aria-label="Why this answer"
            >
              <h2 className="mb-2 font-semibold">Why this answer</h2>
              <p data-testid="why-query-variants">
                {lastTurn?.trace
                  ? <>Searched for: <span className="font-mono">"{lastTurn.trace.resolvedQuery}"</span></>
                  : "Retrieval details aren't kept for past conversations. Ask a new question to see them."}
              </p>
              <p data-testid="why-filters">
                Filters: workspace={activeWorkspace?.name ?? "none"}, collections=
                {availableCollections
                  .filter((c) => selectedCollectionIds.includes(c.id))
                  .map((c) => c.name)
                  .join(",") || "none"}
              </p>
              {lastTurn?.trace ? (
                <p data-testid="why-retrieval-stats" className="font-mono text-xs text-muted-foreground">
                  route={lastTurn.trace.route} · {lastTurn.trace.evidenceCount} source
                  {lastTurn.trace.evidenceCount === 1 ? "" : "s"} · {Math.round(lastTurn.trace.latencyMs)} ms
                </p>
              ) : null}
              <ol data-testid="why-ranked-evidence" className="list-decimal pl-5">
                {!lastTurn || Object.keys(lastTurn.evidenceText).length === 0 ? (
                  <li>No evidence yet</li>
                ) : (
                  dedupeCitations(lastTurn.citations)
                    .sort((a, b) => (b.relevance ?? 0) - (a.relevance ?? 0))
                    .map((meta) => (
                      <li key={meta.evidence_id}>
                        {meta.evidence_id}: {lastTurn.evidenceText[meta.evidence_id] ?? meta.title}
                        {meta.relevance != null ? ` (${Math.round(meta.relevance * 100)}% relevance)` : ""}
                      </li>
                    ))
                )}
              </ol>
              <p data-testid="why-grounding-summary">
                Grounding summary:{" "}
                {(lastTurn?.sentences ?? []).filter((s) => s.support === "supported").length}{" "}
                supported
              </p>
            </aside>
          ) : null}

          {error ? (
            <p role="alert" className="px-4 py-2 text-sm text-destructive">
              {error}
            </p>
          ) : null}

          {loading ? <p role="status" className="px-4 py-2 text-sm">Loading conversation…</p> : null}

          <div
            className="flex-1 space-y-4 overflow-y-auto p-4"
            data-testid="message-list"
            role="log"
            aria-live="polite"
          >
            {turns.length === 0 ? (
              <ChatEmptyState />
            ) : (
              turns.map((turn, index) => {
                const openEvidence = (eid: string) => {
                  setViewerEvidence(eid);
                  setViewerTurn(index);
                  // The citation-viewer dialog is for narrow screens only (lg:hidden) —
                  // at desktop widths the sidebar EvidenceInspector is already visible,
                  // so opening it there would just show an empty backdrop.
                  if (!window.matchMedia("(min-width: 1024px)").matches) {
                    setViewerOpen(true);
                  }
                };
                return (
                  <div key={index} className="space-y-4">
                    <p
                      data-testid="user-message"
                      className="ml-auto max-w-[80%] rounded bg-primary/10 px-3 py-2 text-sm"
                    >
                      {turn.question}
                    </p>
                    {turn.refusalType ? (
                      <RefusalCallout
                        type={turn.refusalType}
                        message={turn.sentences[0]?.text || "Unable to answer"}
                      />
                    ) : turn.sentences.length > 0 ? (
                      <div>
                        <ChatAnswer
                          sentences={turn.sentences}
                          citations={turn.citations}
                          evidenceText={turn.evidenceText}
                          onCite={openEvidence}
                        />
                        {turn.messageId && !responding ? (
                          <FeedbackButtons
                            messageId={turn.messageId}
                            feedback={feedback[turn.messageId] ?? null}
                            onVote={vote}
                          />
                        ) : null}
                      </div>
                    ) : null}
                    {responding && index === turns.length - 1 ? (
                      <ChatThinking streaming={turn.sentences.length > 0} stage={stage} />
                    ) : null}
                  </div>
                );
              })
            )}
          </div>

          <form
            className="border-t border-border p-4"
            data-testid="composer"
            onSubmit={(e) => {
              e.preventDefault();
              void send();
            }}
          >
            <label className="sr-only" htmlFor="chat-input">
              Message
            </label>
            <div className="flex items-end gap-2">
              <textarea
                id="chat-input"
                ref={composerRef}
                rows={1}
                className="max-h-40 flex-1 resize-none overflow-y-auto rounded border border-input bg-background px-3 py-2 text-sm"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    void send();
                  }
                }}
                placeholder="Ask about your documents…"
                disabled={busy || loading}
              />
              <button
                type="submit"
                className="rounded bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-60"
                disabled={busy || loading}
              >
                {busy ? "…" : "Send"}
              </button>
            </div>
            <p className="mt-1.5 px-0.5 text-[11px] text-muted-foreground">
              Enter to send · Shift+Enter for a new line
            </p>
          </form>
        </section>

        <aside
          className="hidden border-l border-border lg:block"
          aria-label="Evidence inspector"
        >
          <EvidenceInspector
            citations={focusCitations}
            evidenceText={focusEvidenceText}
            activeId={viewerEvidence}
            onSelect={setViewerEvidence}
          />
        </aside>
      </div>

      <Dialog open={viewerOpen} onOpenChange={setViewerOpen}>
        <DialogContent data-testid="citation-viewer" className="lg:hidden">
          <DialogHeader>
            <DialogTitle>Sources</DialogTitle>
          </DialogHeader>
          <div className="max-h-[70vh] overflow-y-auto">
            <EvidenceInspector
              citations={focusCitations}
              evidenceText={focusEvidenceText}
              activeId={viewerEvidence}
              onSelect={setViewerEvidence}
            />
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={deleteTarget !== null} onOpenChange={(open) => {
        if (!open && !busy) setDeleteTarget(null);
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete chat?</DialogTitle>
            <DialogDescription>
              Delete “{deleteTarget?.title}” and all its messages? This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          {deleteError ? <p role="alert" className="text-sm text-destructive">{deleteError}</p> : null}
          <DialogFooter>
            <Button variant="outline" disabled={busy} onClick={() => setDeleteTarget(null)}>
              Cancel
            </Button>
            <Button variant="destructive" disabled={busy} onClick={() => void onDeleteChat()}>
              {busy ? "Deleting…" : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
