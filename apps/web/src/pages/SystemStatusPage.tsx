/**
 * @file SystemStatusPage.tsx
 * @description Plain-language "is everything running?" panel — health, readiness, config
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.2.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { useQuery } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";
import { apiJson } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type HealthResponse = { status: string };
type ReadyResponse = { status: string; checks: Record<string, string> };
type EffectiveConfig = {
  config: Record<string, { value: unknown; source: string }>;
  config_hash: string;
};

/** Internal check keys → plain-language labels a non-technical admin recognizes. */
const CHECK_LABELS: Record<string, string> = {
  metadata_store: "Document database",
  queue: "Background jobs",
  vector_alias: "Search index",
  models_service: "AI models",
};

const CONFIG_LABELS: Record<string, string> = {
  sb_tier: "Deployment tier",
  environment: "Environment",
  registration_mode: "Who can sign up",
  public_url: "Public address",
  air_gapped: "Air-gapped (no outbound network)",
  access_token_ttl_min: "Sign-in session length (minutes)",
  bind_host: "Listening address",
  upload_max_bytes: "Maximum upload size (bytes)",
};

function StatusPill({ ok, label }: { ok: boolean; label: string }) {
  return <Badge variant={ok ? "success" : "destructive"}>{label}</Badge>;
}

export function SystemStatusPage() {
  const health = useQuery({
    queryKey: ["system-status", "health"],
    queryFn: () => apiJson<HealthResponse>("/health", { skipAuth: true }),
    retry: false,
  });
  const ready = useQuery({
    queryKey: ["system-status", "ready"],
    queryFn: () => apiJson<ReadyResponse>("/ready", { skipAuth: true }),
    retry: false,
  });
  const config = useQuery({
    queryKey: ["system-status", "config"],
    queryFn: () => apiJson<EffectiveConfig>("/api/v1/admin/effective-config"),
    retry: false,
  });

  const overallOk = health.data?.status === "ok" && ready.data?.status === "ready";
  const anyLoading = health.isLoading || ready.isLoading || config.isLoading;
  const anyError = health.isError || ready.isError || config.isError;

  function refreshAll() {
    void health.refetch();
    void ready.refetch();
    void config.refetch();
  }

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-6 py-10" data-testid="system-status">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Is everything running?</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            A plain-language check of the same signals `npm run doctor` looks at, without
            needing a terminal.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={refreshAll} disabled={anyLoading}>
          <RefreshCw className="h-4 w-4" aria-hidden="true" />
          Refresh
        </Button>
      </div>

      <Card>
        <CardHeader className="flex-row items-center justify-between gap-4 space-y-0">
          <div>
            <CardTitle>Overall status</CardTitle>
            <CardDescription>Combines the app and its background checks.</CardDescription>
          </div>
          {anyLoading ? (
            <Badge variant="outline">Checking…</Badge>
          ) : anyError ? (
            <StatusPill ok={false} label="Could not reach the server" />
          ) : (
            <StatusPill ok={overallOk} label={overallOk ? "Everything's running" : "Needs attention"} />
          )}
        </CardHeader>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Component checks</CardTitle>
          <CardDescription>
            Each part SeismoBrain needs to answer questions about your documents.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {ready.isError ? (
            <p className="text-sm text-destructive" role="alert">
              Couldn't load readiness checks.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Component</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {ready.isLoading
                  ? Array.from({ length: 3 }).map((_, i) => (
                      <TableRow key={i}>
                        <TableCell colSpan={2}>
                          <Skeleton className="h-6 w-full" />
                        </TableCell>
                      </TableRow>
                    ))
                  : Object.entries(ready.data?.checks ?? {}).map(([key, value]) => (
                  <TableRow key={key}>
                    <TableCell>{CHECK_LABELS[key] ?? key}</TableCell>
                    <TableCell>
                      <StatusPill ok={value === "ok"} label={value === "ok" ? "OK" : "Failing"} />
                    </TableCell>
                  </TableRow>
                ))}
                {!ready.isLoading && Object.keys(ready.data?.checks ?? {}).length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={2} className="text-muted-foreground">
                      No checks reported yet.
                    </TableCell>
                  </TableRow>
                ) : null}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Configuration</CardTitle>
          <CardDescription>What this deployment is currently set to.</CardDescription>
        </CardHeader>
        <CardContent>
          {config.isError ? (
            <p className="text-sm text-destructive" role="alert">
              Couldn't load configuration. You may not have admin access.
            </p>
          ) : (
            <Table>
              <TableBody>
                {config.isLoading
                  ? Array.from({ length: 4 }).map((_, i) => (
                      <TableRow key={i}>
                        <TableCell colSpan={2}>
                          <Skeleton className="h-6 w-full" />
                        </TableCell>
                      </TableRow>
                    ))
                  : Object.entries(config.data?.config ?? {}).map(([key, entry]) => (
                  <TableRow key={key}>
                    <TableCell className="text-muted-foreground">
                      {CONFIG_LABELS[key] ?? key}
                    </TableCell>
                    <TableCell>{String(entry.value)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </main>
  );
}
