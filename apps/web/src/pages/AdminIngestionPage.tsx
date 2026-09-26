import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiJson } from "@/api/client";
import type { components } from "@/api/generated/schema";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type Job = components["schemas"]["IngestionJob"];
type Summary = components["schemas"]["IngestionSummary"];
type JobPage = components["schemas"]["JobPage"];
type Action = "retry" | "quarantine" | "release";
const BASE = "/api/v1/admin/ingestion";
const statuses = ["pending", "running", "succeeded", "failed", "dead_letter", "quarantined"];
const label = (value: string) => value.replaceAll("_", " ");
const date = (value?: number | null) => value ? new Date(value * 1000).toLocaleString() : "Not available";
const actionLabels: Record<Action, string> = {
  retry: "Retry job", quarantine: "Quarantine", release: "Release and retry",
};

export function AdminIngestionPage() {
  const client = useQueryClient();
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [collection, setCollection] = useState("");
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [quarantine, setQuarantine] = useState<Job | null>(null);
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState("");
  const limit = 25;

  const summary = useQuery({
    queryKey: ["admin-ingestion", "summary"],
    queryFn: () => apiJson<Summary>(`${BASE}/monitor`),
    refetchInterval: 3000,
    retry: false,
  });
  const params = new URLSearchParams({ search, collection_id: collection, offset: String(offset), limit: String(limit) });
  if (status) params.set("status", status);
  const jobs = useQuery({
    queryKey: ["admin-ingestion", "jobs", search, status, collection, offset],
    queryFn: () => apiJson<JobPage>(`${BASE}/jobs?${params}`),
    refetchInterval: 3000,
    retry: false,
  });
  const detail = useQuery({
    queryKey: ["admin-ingestion", "detail", selected],
    queryFn: () => apiJson<Job>(`${BASE}/jobs/${encodeURIComponent(selected!)}`),
    enabled: selected !== null,
    refetchInterval: 3000,
    retry: false,
  });
  const action = useMutation({
    mutationFn: ({ job, type, reason }: { job: Job; type: Action; reason?: string }) =>
      apiJson<Job>(`${BASE}/jobs/${encodeURIComponent(job.id)}/${type}`, {
        method: "POST",
        ...(type === "quarantine" ? { body: JSON.stringify({ reason }) } : {}),
      }),
    onMutate: () => setMessage(""),
    onSuccess: (job, variables) => {
      setMessage(variables.type === "quarantine"
        ? `${job.filename || job.id} quarantined.`
        : `${job.filename || job.id} queued for processing.`);
      setQuarantine(null);
      setReason("");
    },
    onError: (error) => setMessage(error instanceof ApiError ? error.detail : "Job action failed. Please try again."),
    onSettled: () => { void client.invalidateQueries({ queryKey: ["admin-ingestion"] }); },
  });
  const stale = summary.isError || jobs.isError || summary.fetchStatus === "paused" || jobs.fetchStatus === "paused";
  const counts: [string, number | undefined][] = [
    ["Queued", summary.data?.queue_depth], ["Running", summary.data?.running],
    ["Completed", summary.data?.succeeded], ["Failed", summary.data?.failed],
    ["Dead letters", summary.data?.dead_letter], ["Quarantined", summary.data?.quarantined],
  ];

  function controls(job: Job) {
    return (job.actions ?? []).map((type) => (
      <Button key={type} size="sm" variant="outline" disabled={action.isPending || stale}
        onClick={() => type === "quarantine" ? (setQuarantine(job), setReason("")) : action.mutate({ job, type })}>
        {action.isPending && action.variables?.job.id === job.id && action.variables?.type === type
          ? "Working…" : actionLabels[type]}
      </Button>
    ));
  }

  return (
    <main className="mx-auto max-w-6xl space-y-6 px-6 py-10" data-testid="admin-ingestion">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Ingestion monitor</h1>
          <p className="mt-1 text-sm text-muted-foreground">Document processing, progress, and recovery. Refreshes every 3 seconds.</p>
          <p className="mt-2 text-xs text-muted-foreground">
            {summary.dataUpdatedAt ? `Last summary update: ${new Date(summary.dataUpdatedAt).toLocaleTimeString()}` : "Waiting for the first update…"}
          </p>
        </div>
        <Button variant="outline" onClick={() => void client.invalidateQueries({ queryKey: ["admin-ingestion"] })}>Refresh</Button>
      </div>
      {stale && <p role="alert" className="rounded-md border border-destructive p-3 text-sm text-destructive">
        Could not refresh ingestion data. Previously loaded values may be out of date. Check the connection and refresh.
      </p>}
      {message && <p role="status" className="text-sm">{message}</p>}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-6">
        {counts.map(([name, value]) => <Card key={name}><CardHeader className="pb-2"><CardDescription>{name}</CardDescription></CardHeader>
          <CardContent><p className="text-2xl font-semibold">{value ?? "Not available"}</p></CardContent></Card>)}
      </div>
      <p className="text-xs text-muted-foreground">Counts cover all retained ingestion jobs, independent of the filters below. Dead letters exhausted automatic retries.</p>
      {!!Object.keys(summary.data?.stages ?? {}).length && <p className="text-sm">
        Processing now: {Object.entries(summary.data?.stages ?? {}).map(([stage, count]) => `${stage}: ${count}`).join(" · ")}
      </p>}
      <Card>
        <CardHeader><CardTitle>Jobs</CardTitle><CardDescription>Completed jobs remain here, even when they finish between updates.</CardDescription></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-3">
            <div className="space-y-1"><Label htmlFor="job-search">Search documents</Label>
              <Input id="job-search" value={search} onChange={(e) => { setSearch(e.target.value); setOffset(0); }} placeholder="Filename" /></div>
            <div className="space-y-1"><Label htmlFor="job-status">Status</Label>
              <select id="job-status" className="block h-10 rounded-md border border-input bg-background px-3 text-sm" value={status}
                onChange={(e) => { setStatus(e.target.value); setOffset(0); }}>
                <option value="">All statuses</option>{statuses.map((s) => <option key={s} value={s}>{label(s)}</option>)}
              </select></div>
            <div className="space-y-1"><Label htmlFor="job-collection">Collection ID</Label>
              <Input id="job-collection" value={collection} onChange={(e) => { setCollection(e.target.value); setOffset(0); }} placeholder="All collections" /></div>
          </div>
          {jobs.isLoading && <p role="status">Loading jobs…</p>}
          {jobs.data?.jobs.length === 0 && <p className="py-6 text-sm text-muted-foreground">No ingestion jobs match these filters. Upload a document to begin processing.</p>}
          {!!jobs.data?.jobs.length && <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <caption className="sr-only">Ingestion job history</caption>
              <thead><tr className="border-b">{["Document / collection", "Status / stage", "Attempts", "Updated / duration", "Actions"].map((h) => <th className="p-2" key={h}>{h}</th>)}</tr></thead>
              <tbody>{jobs.data.jobs.map((job) => <tr key={job.id} className="border-b align-top" data-testid="ingestion-job-row">
                <td className="max-w-xs break-words p-2"><span className="font-medium">{job.filename || job.document_id || job.id}</span><div className="text-xs text-muted-foreground">{job.collection_id || "Not available"}</div></td>
                <td className="p-2"><span className="capitalize">{label(job.status ?? "pending")}</span><div className="text-xs text-muted-foreground">{job.stage}</div>
                  {job.error && <p className="mt-1 max-w-xs text-xs text-destructive">{job.error}</p>}</td>
                <td className="p-2">{job.attempts}</td>
                <td className="p-2 text-xs">{date(job.updated_at)}<div>{job.started_at ? `${Math.max(0, (job.ended_at ?? Date.now() / 1000) - job.started_at).toFixed(1)}s` : "Not available"}</div></td>
                <td className="p-2"><div className="flex flex-wrap gap-2"><Button variant="outline" size="sm" onClick={() => setSelected(job.id)}>Details</Button>{controls(job)}</div></td>
              </tr>)}</tbody>
            </table>
          </div>}
          <div className="flex items-center justify-between gap-2 text-sm">
            <span>{jobs.data ? `${jobs.data.total} matching jobs` : "Job count unavailable"}</span>
            <div className="flex gap-2"><Button variant="outline" disabled={offset === 0 || jobs.isFetching} onClick={() => setOffset(Math.max(0, offset - limit))}>Previous</Button>
              <Button variant="outline" disabled={!jobs.data || offset + limit >= jobs.data.total || jobs.isFetching} onClick={() => setOffset(offset + limit)}>Next</Button></div>
          </div>
        </CardContent>
      </Card>
      <Dialog open={selected !== null} onOpenChange={(open) => { if (!open) setSelected(null); }}>
        <DialogContent className="max-h-[85vh] max-w-2xl overflow-y-auto">
          <DialogTitle>{detail.data?.filename || "Job details"}</DialogTitle>
          <DialogDescription>Processing history for job {selected}</DialogDescription>
          {detail.isLoading && <p>Loading history…</p>}
          {(detail.isError || detail.fetchStatus === "paused") && <p role="alert">Could not refresh job history. Any previous history shown may be out of date.</p>}
          {detail.data && <>
            {!detail.data.history_available && <p className="text-sm">This job predates monitoring; earlier stage history is unavailable.</p>}
            {detail.data.quarantine_reason && <p className="text-sm">Quarantine reason: {detail.data.quarantine_reason}</p>}
            {detail.data.error && <p className="text-sm text-destructive">{detail.data.error}</p>}
            <ol className="space-y-3">{detail.data.events?.map((event, i) => <li key={i} className="border-l-2 pl-3 text-sm">
              <p className="font-medium">{event.stage} · {label(event.status)}</p>
              <p className="text-xs text-muted-foreground">{date(event.timestamp)} · attempt {event.attempt}{event.duration_ms != null ? ` · ${Math.round(event.duration_ms)}ms` : ""}</p>
              {!!Object.keys(event.counts ?? {}).length && <p>{Object.entries(event.counts ?? {}).map(([key, count]) => `${count} ${key}`).join(" · ")}</p>}
              {event.error && <p className="text-destructive">{event.error}</p>}
              {event.reason && <p>Reason: {event.reason}</p>}
              {event.actor && <p className="text-xs">By {event.actor}</p>}
            </li>)}</ol>
          </>}
        </DialogContent>
      </Dialog>
      <Dialog open={quarantine !== null} onOpenChange={(open) => { if (!open) setQuarantine(null); }}>
        <DialogContent><DialogTitle>Quarantine {quarantine?.filename || "job"}</DialogTitle>
          <DialogDescription>Processing will stop at the next safe stage boundary. Release will rerun processing from the source.</DialogDescription>
          <Label htmlFor="quarantine-reason">Reason</Label><Input id="quarantine-reason" value={reason} maxLength={500} onChange={(e) => setReason(e.target.value)} />
          {action.isError && <p role="alert" className="text-sm text-destructive">{message}</p>}
          <Button disabled={!reason.trim() || action.isPending} onClick={() => quarantine && action.mutate({ job: quarantine, type: "quarantine", reason: reason.trim() })}>Quarantine job</Button>
        </DialogContent>
      </Dialog>
    </main>
  );
}
