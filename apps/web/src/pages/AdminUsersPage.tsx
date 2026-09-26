/**
 * @file AdminUsersPage.tsx
 * @description Admin user management: search, approve/disable, role, force sign-out
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.4.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import {
  approveUser,
  disableUser,
  forceSignOut,
  listUsers,
  setUserRole,
  type UserRow,
} from "@/api/services/users";
import { useSession } from "@/auth/session";
import { usePagination } from "@/lib/pagination";
import { sortByKey, type SortDirection } from "@/lib/sort";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Pagination } from "@/components/ui/pagination";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  SortButton,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { toast } from "@/components/ui/sonner";

type SortKey = "name" | "status" | "role";

export function AdminUsersPage() {
  const me = useSession((s) => s.user);
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("name");
  const [sortDir, setSortDir] = useState<SortDirection>("asc");

  const q = useQuery({ queryKey: ["admin-users"], queryFn: listUsers });
  const users = q.data?.users ?? [];
  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return users;
    return users.filter(
      (u) => u.name.toLowerCase().includes(term) || u.email.toLowerCase().includes(term),
    );
  }, [users, search]);
  const sorted = useMemo(() => {
    const keyFn: (u: UserRow) => string =
      sortKey === "name"
        ? (u) => u.name.toLowerCase()
        : sortKey === "status"
          ? (u) => u.status
          : (u) => u.system_role;
    return sortByKey(filtered, keyFn, sortDir);
  }, [filtered, sortKey, sortDir]);
  const { page, setPage, totalPages, pageItems } = usePagination(sorted, 20);

  function toggleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

  function onError(err: unknown, fallback: string) {
    toast.error(err instanceof ApiError ? err.detail : fallback);
  }

  const approve = useMutation({
    mutationFn: approveUser,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-users"] }),
    onError: (err) => onError(err, "Couldn't approve that user"),
  });
  const disable = useMutation({
    mutationFn: disableUser,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-users"] }),
    onError: (err) => onError(err, "Couldn't disable that user"),
  });
  const changeRole = useMutation({
    mutationFn: ({ id, role }: { id: string; role: "system_admin" | "user" }) =>
      setUserRole(id, role),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-users"] }),
    onError: (err) => onError(err, "Couldn't change that role"),
  });
  const signOut = useMutation({
    mutationFn: forceSignOut,
    onSuccess: (result) => toast.success(`Signed out everywhere (${result.revoked_families} device(s)).`),
    onError: (err) => onError(err, "Couldn't sign that user out"),
  });

  return (
    <main className="mx-auto max-w-4xl space-y-4 px-6 py-10" data-testid="admin-users">
      <h1 className="text-3xl font-semibold tracking-tight">Users</h1>
      <Input
        className="max-w-sm"
        placeholder="Search by name or email…"
        aria-label="Search users"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      {/* Below md: stacked cards instead of a horizontally-scrolling table. */}
      <div className="space-y-3 md:hidden">
        {q.isLoading
          ? Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-28 w-full" />)
          : pageItems.map((u: UserRow) => (
              <Card key={u.id} className="p-4">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="truncate font-medium">{u.name}</p>
                    <p className="truncate text-sm text-muted-foreground">{u.email}</p>
                  </div>
                  <Badge
                    variant={
                      u.status === "active" ? "success" : u.status === "pending" ? "outline" : "destructive"
                    }
                  >
                    {u.status}
                  </Badge>
                </div>
                <div className="mt-3">
                  <Select
                    value={u.system_role}
                    onValueChange={(value) =>
                      changeRole.mutate({ id: u.id, role: value as "system_admin" | "user" })
                    }
                    disabled={u.id === me?.id}
                  >
                    <SelectTrigger className="h-8 w-full" aria-label={`Role for ${u.name}`}>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="user">Member</SelectItem>
                      <SelectItem value="system_admin">Admin</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {u.status === "pending" ? (
                    <Button size="sm" onClick={() => approve.mutate(u.id)} disabled={approve.isPending}>
                      Approve
                    </Button>
                  ) : null}
                  {u.status === "active" ? (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => disable.mutate(u.id)}
                      disabled={disable.isPending || u.id === me?.id}
                    >
                      Disable
                    </Button>
                  ) : null}
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => signOut.mutate(u.id)}
                    disabled={signOut.isPending}
                  >
                    Force sign-out
                  </Button>
                </div>
              </Card>
            ))}
      </div>

      <div className="hidden md:block">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>
                <SortButton
                  label="Person"
                  active={sortKey === "name"}
                  direction={sortDir}
                  onClick={() => toggleSort("name")}
                />
              </TableHead>
              <TableHead>
                <SortButton
                  label="Status"
                  active={sortKey === "status"}
                  direction={sortDir}
                  onClick={() => toggleSort("status")}
                />
              </TableHead>
              <TableHead>
                <SortButton
                  label="Role"
                  active={sortKey === "role"}
                  direction={sortDir}
                  onClick={() => toggleSort("role")}
                />
              </TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {q.isLoading
              ? Array.from({ length: 4 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell colSpan={4}>
                      <Skeleton className="h-8 w-full" />
                    </TableCell>
                  </TableRow>
                ))
              : pageItems.map((u: UserRow) => (
              <TableRow key={u.id}>
                <TableCell>
                  <div className="font-medium">{u.name}</div>
                  <div className="text-muted-foreground">{u.email}</div>
                </TableCell>
                <TableCell>
                  <Badge variant={u.status === "active" ? "success" : u.status === "pending" ? "outline" : "destructive"}>
                    {u.status}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Select
                    value={u.system_role}
                    onValueChange={(value) =>
                      changeRole.mutate({ id: u.id, role: value as "system_admin" | "user" })
                    }
                    disabled={u.id === me?.id}
                  >
                    <SelectTrigger className="h-8 w-36" aria-label={`Role for ${u.name}`}>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="user">Member</SelectItem>
                      <SelectItem value="system_admin">Admin</SelectItem>
                    </SelectContent>
                  </Select>
                </TableCell>
                <TableCell className="space-x-1 text-right">
                  {u.status === "pending" ? (
                    <Button size="sm" onClick={() => approve.mutate(u.id)} disabled={approve.isPending}>
                      Approve
                    </Button>
                  ) : null}
                  {u.status === "active" ? (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => disable.mutate(u.id)}
                      disabled={disable.isPending || u.id === me?.id}
                    >
                      Disable
                    </Button>
                  ) : null}
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => signOut.mutate(u.id)}
                    disabled={signOut.isPending}
                  >
                    Force sign-out
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      {!q.isLoading && filtered.length === 0 ? (
        <EmptyState title={search ? "No one matches that search." : "No users yet."} />
      ) : null}
      <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
    </main>
  );
}
