/**
 * @file GlossaryPage.tsx
 * @description Dictionary (glossary) and document numbering (identifier patterns) editor
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.1.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Plus, Trash2 } from "lucide-react";
import { ApiError } from "@/api/client";
import {
  getGlossary,
  putGlossary,
  putIdentifierPatterns,
  type GlossaryEntry,
  type IdentifierPattern,
} from "@/api/services/glossary";
import { listWorkspaces } from "@/api/services/workspaces";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "@/components/ui/sonner";

export function GlossaryPage() {
  const [workspaceId, setWorkspaceId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [entries, setEntries] = useState<GlossaryEntry[]>([]);
  const [patterns, setPatterns] = useState<IdentifierPattern[]>([]);

  const workspacesQuery = useQuery({ queryKey: ["admin-workspaces-picker"], queryFn: listWorkspaces });
  const workspaces = workspacesQuery.data?.workspaces ?? [];

  useEffect(() => {
    const first = workspaces[0];
    if (first && !workspaceId) setWorkspaceId(first.id);
  }, [workspaces, workspaceId]);

  const glossaryQuery = useQuery({
    queryKey: ["glossary", workspaceId],
    enabled: Boolean(workspaceId),
    queryFn: () => getGlossary(workspaceId),
  });

  useEffect(() => {
    if (glossaryQuery.data) {
      setEntries(glossaryQuery.data.glossary);
      setPatterns(glossaryQuery.data.identifier_patterns);
    }
  }, [glossaryQuery.data]);

  async function onSaveGlossary() {
    setError(null);
    setBusy(true);
    try {
      const cleaned = entries.filter((e) => e.term.trim() && e.expansion.trim());
      await putGlossary(workspaceId, cleaned);
      setEntries(cleaned);
      toast.success("Dictionary saved.");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Couldn't save the dictionary");
    } finally {
      setBusy(false);
    }
  }

  async function onSavePatterns() {
    setError(null);
    setBusy(true);
    try {
      const cleaned = patterns.filter((p) => p.name.trim() && p.pattern.trim());
      await putIdentifierPatterns(workspaceId, cleaned);
      setPatterns(cleaned);
      toast.success("Document numbering patterns saved.");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Couldn't save the patterns");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-6 py-10" data-testid="glossary-page">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Dictionary & document numbering</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Teach SeismoBrain your abbreviations and part-number formats so search understands
          them. For example, "PPE" means "personal protective equipment," or "P2/94" is a flange code.
        </p>
      </div>

      {error ? (
        <p role="alert" className="text-sm text-destructive" data-testid="glossary-error">
          {error}
        </p>
      ) : null}

      <div className="space-y-1.5">
        <Label htmlFor="glossary-ws">Workspace</Label>
        <Select value={workspaceId} onValueChange={setWorkspaceId}>
          <SelectTrigger id="glossary-ws" className="max-w-sm" aria-label="Workspace">
            <SelectValue placeholder="Choose a workspace" />
          </SelectTrigger>
          <SelectContent>
            {workspaces.map((ws) => (
              <SelectItem key={ws.id} value={ws.id}>
                {ws.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Tabs defaultValue="dictionary">
        <TabsList>
          <TabsTrigger value="dictionary">Dictionary</TabsTrigger>
          <TabsTrigger value="numbering">Document numbering</TabsTrigger>
        </TabsList>

        <TabsContent value="dictionary" className="space-y-3">
          {entries.map((entry, i) => (
            <div key={i} className="flex items-center gap-2">
              <Input
                aria-label="Term"
                placeholder="Term (e.g. PPE)"
                value={entry.term}
                onChange={(e) =>
                  setEntries((prev) =>
                    prev.map((it, idx) => (idx === i ? { ...it, term: e.target.value } : it)),
                  )
                }
              />
              <Input
                aria-label="Expansion"
                placeholder="Means (e.g. personal protective equipment)"
                value={entry.expansion}
                onChange={(e) =>
                  setEntries((prev) =>
                    prev.map((it, idx) => (idx === i ? { ...it, expansion: e.target.value } : it)),
                  )
                }
              />
              <Button
                variant="ghost"
                size="icon"
                aria-label="Remove entry"
                onClick={() => setEntries((prev) => prev.filter((_, idx) => idx !== i))}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setEntries((prev) => [...prev, { term: "", expansion: "" }])}
          >
            <Plus className="h-4 w-4" aria-hidden="true" />
            Add term
          </Button>
          <div>
            <Button disabled={!workspaceId || busy} onClick={() => void onSaveGlossary()}>
              {busy ? "Saving…" : "Save dictionary"}
            </Button>
          </div>
        </TabsContent>

        <TabsContent value="numbering" className="space-y-3">
          {patterns.map((pattern, i) => (
            <div key={i} className="flex items-center gap-2">
              <Input
                aria-label="Pattern name"
                placeholder="Name (e.g. flange code)"
                value={pattern.name}
                onChange={(e) =>
                  setPatterns((prev) =>
                    prev.map((it, idx) => (idx === i ? { ...it, name: e.target.value } : it)),
                  )
                }
              />
              <Input
                aria-label="Pattern"
                placeholder="Pattern (e.g. P\d+/\d+)"
                value={pattern.pattern}
                onChange={(e) =>
                  setPatterns((prev) =>
                    prev.map((it, idx) => (idx === i ? { ...it, pattern: e.target.value } : it)),
                  )
                }
              />
              <Button
                variant="ghost"
                size="icon"
                aria-label="Remove pattern"
                onClick={() => setPatterns((prev) => prev.filter((_, idx) => idx !== i))}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              setPatterns((prev) => [...prev, { name: "", pattern: "", confidence: "high" }])
            }
          >
            <Plus className="h-4 w-4" aria-hidden="true" />
            Add pattern
          </Button>
          <div>
            <Button disabled={!workspaceId || busy} onClick={() => void onSavePatterns()}>
              {busy ? "Saving…" : "Save patterns"}
            </Button>
          </div>
        </TabsContent>
      </Tabs>
    </main>
  );
}
