/**
 * @file AdminWorkspacesPage.tsx
 * @description Workspaces, collections, merged ACL editor (direct + team grants), research toggle
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.4.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { listGrantsForResource } from "@/api/services/groups";
import {
  listWorkspaceCollections,
  listWorkspaces,
  setCollectionAcl,
  setResearchEnabled,
} from "@/api/services/workspaces";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "@/components/ui/sonner";

export function AdminWorkspacesPage() {
  const qc = useQueryClient();
  const [selectedWs, setSelectedWs] = useState("");
  const [selectedCol, setSelectedCol] = useState("");
  const [principal, setPrincipal] = useState("");
  const [permission, setPermission] = useState<"read" | "write">("read");
  const [error, setError] = useState<string | null>(null);

  const workspaces = useQuery({ queryKey: ["admin-workspaces"], queryFn: listWorkspaces });
  const activeWorkspace = workspaces.data?.workspaces.find((w) => w.id === selectedWs);

  const collections = useQuery({
    queryKey: ["admin-collections", selectedWs],
    enabled: Boolean(selectedWs),
    queryFn: () => listWorkspaceCollections(selectedWs),
  });
  const active = collections.data?.collections.find((c) => c.id === selectedCol);

  const teamGrants = useQuery({
    queryKey: ["team-grants", "collection", selectedCol],
    enabled: Boolean(selectedCol),
    queryFn: () => listGrantsForResource("collection", selectedCol),
  });

  const saveAcl = useMutation({
    mutationFn: async () => {
      if (!active) throw new Error("Select a collection");
      const entries = [
        ...(active.acl ?? []).map((e) => ({
          principal: e.principal || e.user_id || "",
          permission: e.permission || "read",
        })),
        { principal, permission },
      ].filter((e) => e.principal);
      return setCollectionAcl(selectedCol, entries);
    },
    onSuccess: async () => {
      setPrincipal("");
      setError(null);
      await qc.invalidateQueries({ queryKey: ["admin-collections", selectedWs] });
    },
    onError: (err) => {
      setError(err instanceof ApiError ? err.detail : "Failed to update access");
    },
  });

  const research = useMutation({
    mutationFn: (enabled: boolean) => setResearchEnabled(selectedWs, enabled),
    onSuccess: async (result) => {
      toast.success(result.research_enabled ? "Deep research mode enabled." : "Deep research mode disabled.");
      await qc.invalidateQueries({ queryKey: ["admin-workspaces"] });
    },
    onError: (err) => toast.error(err instanceof ApiError ? err.detail : "Couldn't change that setting"),
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    saveAcl.mutate();
  }

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-6 py-10" data-testid="admin-workspaces">
      <h1 className="text-3xl font-semibold tracking-tight">Workspaces</h1>
      {error ? (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      ) : null}

      <div className="space-y-1.5">
        <Label htmlFor="ws-select">Workspace</Label>
        <Select
          value={selectedWs}
          onValueChange={(value) => {
            setSelectedWs(value);
            setSelectedCol("");
          }}
        >
          <SelectTrigger id="ws-select" className="max-w-sm" aria-label="Workspace">
            <SelectValue placeholder="Select…" />
          </SelectTrigger>
          <SelectContent>
            {(workspaces.data?.workspaces ?? []).map((w) => (
              <SelectItem key={w.id} value={w.id}>
                {w.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {activeWorkspace ? (
        <section className="flex items-center justify-between rounded-md border border-border p-4">
          <div>
            <p className="font-medium">Deep research mode</p>
            <p className="text-sm text-muted-foreground">
              Lets people in this workspace ask multi-step questions that plan and run several
              searches. Off by default.
            </p>
          </div>
          <Button
            variant={activeWorkspace.research_enabled ? "outline" : "default"}
            size="sm"
            disabled={research.isPending}
            onClick={() => research.mutate(!activeWorkspace.research_enabled)}
          >
            {activeWorkspace.research_enabled ? "Disable" : "Enable"}
          </Button>
        </section>
      ) : null}

      {selectedWs ? (
        <div className="space-y-1.5">
          <Label htmlFor="col-select">Collection</Label>
          <Select value={selectedCol} onValueChange={setSelectedCol}>
            <SelectTrigger id="col-select" className="max-w-sm" aria-label="Collection">
              <SelectValue placeholder="Select…" />
            </SelectTrigger>
            <SelectContent>
              {(collections.data?.collections ?? []).map((c) => (
                <SelectItem key={c.id} value={c.id}>
                  {c.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      ) : null}

      {active ? (
        <section className="space-y-3" data-testid="acl-editor">
          <h2 className="text-lg font-medium">Who can access "{active.name}"</h2>

          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Direct access
            </p>
            <ul className="divide-y rounded-md border border-border text-sm">
              {(active.acl ?? []).length === 0 ? (
                <li className="px-3 py-2 text-muted-foreground">No one added directly yet.</li>
              ) : (
                (active.acl ?? []).map((e, i) => (
                  <li key={`${e.principal ?? e.user_id}-${i}`} className="px-3 py-2">
                    {e.principal || e.user_id} · {e.permission || "read"}
                  </li>
                ))
              )}
            </ul>
          </div>

          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Via teams
            </p>
            <ul className="divide-y rounded-md border border-border text-sm">
              {(teamGrants.data?.grants ?? []).length === 0 ? (
                <li className="px-3 py-2 text-muted-foreground">No team has access yet.</li>
              ) : (
                (teamGrants.data?.grants ?? []).map((g) => (
                  <li key={g.group_id} className="flex items-center justify-between px-3 py-2">
                    <span>{g.group_name}</span>
                    <Badge variant="secondary">{g.permission}</Badge>
                  </li>
                ))
              )}
            </ul>
            <p className="mt-1 text-xs text-muted-foreground">
              Manage team grants from the Teams page.
            </p>
          </div>

          <form className="flex flex-wrap items-end gap-2" onSubmit={onSubmit}>
            <div className="space-y-1">
              <Label htmlFor="principal" required>
                Add a person by user id
              </Label>
              <Input
                id="principal"
                value={principal}
                onChange={(e) => setPrincipal(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="permission">Permission</Label>
              <Select value={permission} onValueChange={(v) => setPermission(v as "read" | "write")}>
                <SelectTrigger id="permission" className="w-28">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="read">Read</SelectItem>
                  <SelectItem value="write">Write</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button type="submit" disabled={saveAcl.isPending}>
              Add
            </Button>
          </form>
        </section>
      ) : null}
    </main>
  );
}
