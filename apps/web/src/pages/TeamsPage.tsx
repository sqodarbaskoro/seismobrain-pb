/**
 * @file TeamsPage.tsx
 * @description Teams (groups): membership and broad collection/document grants
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.2.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";
import { ApiError } from "@/api/client";
import {
  addMember,
  createGroup,
  getGroup,
  grantPermission,
  listGroups,
  removeMember,
  type Permission,
  type ResourceType,
} from "@/api/services/groups";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "@/components/ui/sonner";

export function TeamsPage() {
  const qc = useQueryClient();
  const [newTeamName, setNewTeamName] = useState("");
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null);
  const [newMember, setNewMember] = useState("");
  const [grantResourceType, setGrantResourceType] = useState<ResourceType>("collection");
  const [grantResourceId, setGrantResourceId] = useState("");
  const [grantPerm, setGrantPerm] = useState<Permission>("read");

  const groupsQuery = useQuery({ queryKey: ["teams"], queryFn: listGroups });
  const groups = groupsQuery.data?.groups ?? [];

  const detailQuery = useQuery({
    queryKey: ["team", selectedGroupId],
    enabled: Boolean(selectedGroupId),
    queryFn: () => getGroup(selectedGroupId as string),
  });

  function onErr(err: unknown, fallback: string) {
    toast.error(err instanceof ApiError ? err.detail : fallback);
  }

  const create = useMutation({
    mutationFn: () => createGroup(newTeamName.trim()),
    onSuccess: async (created) => {
      setNewTeamName("");
      await qc.invalidateQueries({ queryKey: ["teams"] });
      setSelectedGroupId(created.id);
    },
    onError: (err) => onErr(err, "Couldn't create the team"),
  });

  const addMemberMutation = useMutation({
    mutationFn: () => addMember(selectedGroupId as string, newMember.trim()),
    onSuccess: async () => {
      setNewMember("");
      await qc.invalidateQueries({ queryKey: ["team", selectedGroupId] });
      await qc.invalidateQueries({ queryKey: ["teams"] });
    },
    onError: (err) => onErr(err, "Couldn't add that member"),
  });

  const removeMemberMutation = useMutation({
    mutationFn: (userId: string) => removeMember(selectedGroupId as string, userId),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["team", selectedGroupId] });
      await qc.invalidateQueries({ queryKey: ["teams"] });
    },
    onError: (err) => onErr(err, "Couldn't remove that member"),
  });

  const grant = useMutation({
    mutationFn: () =>
      grantPermission(selectedGroupId as string, grantResourceType, grantResourceId.trim(), grantPerm),
    onSuccess: () => {
      toast.success(`Granted ${grantPerm} on ${grantResourceType} "${grantResourceId}".`);
      setGrantResourceId("");
    },
    onError: (err) => onErr(err, "Couldn't grant access"),
  });

  const detail = detailQuery.data;

  return (
    <main className="mx-auto max-w-4xl px-6 py-10" data-testid="teams-page">
      <h1 className="text-3xl font-semibold tracking-tight">Teams</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Group people so you can grant a collection to everyone on a team at once, instead of
        one person at a time.
      </p>

      <div className="mt-6 grid gap-6 md:grid-cols-[16rem_1fr]">
        <div className="space-y-3">
          <div className="flex gap-2">
            <Input
              placeholder="New team name"
              aria-label="New team name"
              value={newTeamName}
              onChange={(e) => setNewTeamName(e.target.value)}
            />
            <Button
              size="sm"
              disabled={!newTeamName.trim() || create.isPending}
              onClick={() => create.mutate()}
            >
              Add
            </Button>
          </div>
          {groupsQuery.isLoading ? (
            <div className="space-y-2" data-testid="team-list">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-9 w-full" />
              ))}
            </div>
          ) : (
            <ul className="divide-y rounded-md border border-border" data-testid="team-list">
              {groups.map((g) => (
                <li key={g.id}>
                  <button
                    type="button"
                    className={`block w-full px-3 py-2 text-left text-sm hover:bg-foreground/5 ${
                      g.id === selectedGroupId ? "bg-primary/10 font-medium" : ""
                    }`}
                    onClick={() => setSelectedGroupId(g.id)}
                  >
                    {g.name}
                    <span className="ml-2 text-xs text-muted-foreground">
                      {g.member_count} member{g.member_count === 1 ? "" : "s"}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
          {!groupsQuery.isLoading && groups.length === 0 ? (
            <EmptyState title="No teams yet." />
          ) : null}
        </div>

        {detail ? (
          <div className="space-y-6" data-testid="team-detail">
            <section className="space-y-2">
              <h2 className="text-lg font-medium">{detail.name}: members</h2>
              {detail.members.length === 0 ? (
                <EmptyState title="No members yet." />
              ) : (
              <ul className="divide-y rounded-md border border-border text-sm">
                {detail.members.map((userId) => (
                  <li key={userId} className="flex items-center justify-between px-3 py-2">
                    {userId}
                    <Button
                      variant="ghost"
                      size="icon"
                      aria-label={`Remove ${userId}`}
                      onClick={() => removeMemberMutation.mutate(userId)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </li>
                ))}
              </ul>
              )}
              <div className="flex gap-2">
                <Input
                  placeholder="User id to add"
                  aria-label="User id to add"
                  value={newMember}
                  onChange={(e) => setNewMember(e.target.value)}
                />
                <Button
                  size="sm"
                  variant="outline"
                  disabled={!newMember.trim() || addMemberMutation.isPending}
                  onClick={() => addMemberMutation.mutate()}
                >
                  Add member
                </Button>
              </div>
            </section>

            <section className="space-y-2 rounded-md border border-border p-4">
              <h2 className="text-lg font-medium">Grant this team access</h2>
              <p className="text-sm text-muted-foreground">
                Every member gets this permission on the collection or document. It is visible
                alongside its direct access list on the Workspaces page.
              </p>
              <div className="flex flex-wrap items-end gap-2">
                <div className="space-y-1">
                  <Label>Type</Label>
                  <Select value={grantResourceType} onValueChange={(v) => setGrantResourceType(v as ResourceType)}>
                    <SelectTrigger className="w-32" aria-label="Resource type">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="collection">Collection</SelectItem>
                      <SelectItem value="document">Document</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1">
                  <Label htmlFor="grant-resource-id">Collection or document id</Label>
                  <Input
                    id="grant-resource-id"
                    value={grantResourceId}
                    onChange={(e) => setGrantResourceId(e.target.value)}
                  />
                </div>
                <div className="space-y-1">
                  <Label>Permission</Label>
                  <Select value={grantPerm} onValueChange={(v) => setGrantPerm(v as Permission)}>
                    <SelectTrigger className="w-28" aria-label="Permission">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="read">Read</SelectItem>
                      <SelectItem value="write">Write</SelectItem>
                      <SelectItem value="manage">Manage</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button disabled={!grantResourceId.trim() || grant.isPending} onClick={() => grant.mutate()}>
                  Grant
                </Button>
              </div>
            </section>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">Choose a team to manage it.</p>
        )}
      </div>
    </main>
  );
}
