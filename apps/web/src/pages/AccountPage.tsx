/**
 * @file AccountPage.tsx
 * @description Self-service security: your active sessions and API keys
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-19
 * @version 0.2.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import {
  API_KEY_SCOPES,
  type ApiKeyScope,
  issueApiToken,
  listApiTokens,
  listSessions,
  deleteApiToken,
  revokeSession,
} from "@/api/services/account";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { toast } from "@/components/ui/sonner";

const TOKEN_TTL_SECONDS = 60 * 60 * 24 * 90; // matches the server's max (T04.5)
const ALL_SCOPES: ApiKeyScope[] = API_KEY_SCOPES.map((s) => s.value);

function formatWhen(unixSeconds: number): string {
  if (!unixSeconds) return "Not available";
  return new Date(unixSeconds * 1000).toLocaleString();
}

export function AccountPage() {
  const qc = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [tokenName, setTokenName] = useState("");
  const [revealedToken, setRevealedToken] = useState<string | null>(null);

  const sessionsQuery = useQuery({ queryKey: ["my-sessions"], queryFn: listSessions });
  const tokensQuery = useQuery({ queryKey: ["my-api-tokens"], queryFn: listApiTokens });

  function onErr(err: unknown, fallback: string) {
    toast.error(err instanceof ApiError ? err.detail : fallback);
  }

  const revokeSessionMutation = useMutation({
    mutationFn: revokeSession,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["my-sessions"] }),
    onError: (err) => onErr(err, "Couldn't sign out that device"),
  });

  const createToken = useMutation({
    mutationFn: () =>
      issueApiToken({
        name: tokenName.trim(),
        scopes: ALL_SCOPES,
        ttl_seconds: TOKEN_TTL_SECONDS,
      }),
    onSuccess: async (result) => {
      setRevealedToken(result.token);
      setTokenName("");
      await qc.invalidateQueries({ queryKey: ["my-api-tokens"] });
    },
    onError: (err) => onErr(err, "Couldn't create that key"),
  });

  const deleteTokenMutation = useMutation({
    mutationFn: deleteApiToken,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["my-api-tokens"] }),
    onError: (err) => onErr(err, "Couldn't delete that key"),
  });

  return (
    <main className="mx-auto max-w-3xl space-y-8 px-6 py-10" data-testid="account-page">
      <h1 className="text-3xl font-semibold tracking-tight">Your account</h1>

      <section className="space-y-3">
        <div>
          <h2 className="text-lg font-medium">Active sessions</h2>
          <p className="text-sm text-muted-foreground">
            Every device currently signed in as you. Signing out a device you're using right
            now will sign you out here too.
          </p>
        </div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Device</TableHead>
              <TableHead>Signed in</TableHead>
              <TableHead className="text-right">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(sessionsQuery.data?.sessions ?? []).map((s) => (
              <TableRow key={s.id}>
                <TableCell>{s.user_agent || "Unknown device"}</TableCell>
                <TableCell className="text-muted-foreground">{formatWhen(s.created_at)}</TableCell>
                <TableCell className="text-right">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={revokeSessionMutation.isPending}
                    onClick={() => revokeSessionMutation.mutate(s.id)}
                  >
                    Sign out
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {!sessionsQuery.isLoading && (sessionsQuery.data?.sessions.length ?? 0) === 0 ? (
          <p className="text-sm text-muted-foreground">No active sessions found.</p>
        ) : null}
      </section>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-medium">API keys</h2>
            <p className="text-sm text-muted-foreground">
              For scripts or tools that call SeismoBrain on your behalf.
            </p>
          </div>
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            New key
          </Button>
        </div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Scopes</TableHead>
              <TableHead>Expires</TableHead>
              <TableHead className="text-right">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(tokensQuery.data?.tokens ?? []).map((t) => (
              <TableRow key={t.id}>
                <TableCell>{t.name}</TableCell>
                <TableCell className="text-muted-foreground">{t.scopes.join(", ")}</TableCell>
                <TableCell className="text-muted-foreground">{formatWhen(t.expires_at)}</TableCell>
                <TableCell className="text-right">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={deleteTokenMutation.isPending}
                    onClick={() => deleteTokenMutation.mutate(t.id)}
                  >
                    Delete
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {!tokensQuery.isLoading && (tokensQuery.data?.tokens.length ?? 0) === 0 ? (
          <p className="text-sm text-muted-foreground">No API keys yet.</p>
        ) : null}
      </section>

      <Dialog
        open={createOpen}
        onOpenChange={(open) => {
          setCreateOpen(open);
          if (!open) setRevealedToken(null);
        }}
      >
        <DialogContent>
          {revealedToken ? (
            <>
              <DialogHeader>
                <DialogTitle>Copy your key now</DialogTitle>
                <DialogDescription>
                  This is the only time it's shown. You'll need to create a new one if you
                  lose it.
                </DialogDescription>
              </DialogHeader>
              <p className="break-all rounded-md border border-border bg-muted/50 p-3 font-mono text-sm">
                {revealedToken}
              </p>
              <div className="space-y-1.5">
                <Label>Example request</Label>
                <pre className="overflow-x-auto rounded-md border border-border bg-muted/50 p-3 font-mono text-xs">
                  {`export SEISMOBRAIN_API_KEY=<paste the key above>\ncurl -H "Authorization: Bearer $SEISMOBRAIN_API_KEY" \\\n  ${window.location.origin}/api/v1/collections`}
                </pre>
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => {
                    void navigator.clipboard.writeText(
                      `export SEISMOBRAIN_API_KEY=${revealedToken}\ncurl -H "Authorization: Bearer $SEISMOBRAIN_API_KEY" \\\n  ${window.location.origin}/api/v1/collections`
                    );
                    toast.success("Copied example.");
                  }}
                >
                  Copy example
                </Button>
                <Button
                  onClick={() => {
                    void navigator.clipboard.writeText(revealedToken);
                    toast.success("Copied.");
                  }}
                >
                  Copy key
                </Button>
                <Button variant="outline" onClick={() => setCreateOpen(false)}>
                  Done
                </Button>
              </DialogFooter>
            </>
          ) : (
            <>
              <DialogHeader>
                <DialogTitle>New API key</DialogTitle>
                <DialogDescription>
                  Valid for 90 days from creation, then it stops working. Create a new one when
                  it expires. The secret is shown once, right after you create it; SeismoBrain
                  never displays it again.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-3">
                <div className="space-y-1.5">
                  <Label htmlFor="token-name">Name</Label>
                  <Input
                    id="token-name"
                    placeholder="e.g. reporting script"
                    value={tokenName}
                    onChange={(e) => setTokenName(e.target.value)}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Permissions</Label>
                  {API_KEY_SCOPES.map((scope) => (
                    <label
                      key={scope.value}
                      className="flex items-start gap-2 rounded-md border border-border p-2 text-sm"
                    >
                      <input type="checkbox" checked disabled className="mt-0.5" />
                      <span>
                        <span className="font-medium">{scope.label}</span>
                        <span className="block text-muted-foreground">{scope.description}</span>
                      </span>
                    </label>
                  ))}
                  <p className="text-xs text-muted-foreground">
                    This key can only ever do what you can already do. It never grants more
                    access than your own account has.
                  </p>
                </div>
              </div>
              <DialogFooter>
                <Button
                  disabled={!tokenName.trim() || createToken.isPending}
                  onClick={() => createToken.mutate()}
                >
                  Create
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </main>
  );
}
