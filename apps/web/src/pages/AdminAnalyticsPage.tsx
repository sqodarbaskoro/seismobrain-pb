/**
 * @file AdminAnalyticsPage.tsx
 * @description Admin metrics dashboard: usage, latency, refusals, feedback, and the
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-26
 * @modified 2026-09-26
 * @version 0.1.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 * questions the system couldn't answer, off GET /api/v1/admin/analytics (FR-ADM-08)
 */

import { useQuery } from "@tanstack/react-query";
import { apiJson } from "@/api/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

type AnalyticsSnapshot = {
  usage: { total: number; by_route: Record<string, number> };
  refusal_mix: Record<string, number>;
  latency: { p95_ms: number; samples: number };
  top_unanswered_questions: { question: string; count: number }[];
  feedback_trends: { by_rating: Record<string, number>; by_reason: Record<string, number> };
};

function sum(counts: Record<string, number>): number {
  return Object.values(counts).reduce((a, b) => a + b, 0);
}

function StatTile({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
        <p className="mt-1 font-mono text-2xl font-semibold tabular-nums">{value}</p>
        {hint ? <p className="mt-0.5 text-xs text-muted-foreground">{hint}</p> : null}
      </CardContent>
    </Card>
  );
}

/**
 * A handful of counted categories ranked by size — too few and too static for a
 * time-series chart, so a labeled bar list (one hue, magnitude-only) rather than a
 * chart-library dependency. `barClassName` carries status meaning (e.g. destructive
 * for refusals) when the whole list represents one status, not distinct identities.
 */
function BarList({
  entries,
  barClassName = "bg-primary",
  emptyLabel,
}: {
  entries: [string, number][];
  barClassName?: string;
  emptyLabel: string;
}) {
  if (entries.length === 0) {
    return <p className="text-sm text-muted-foreground">{emptyLabel}</p>;
  }
  const max = Math.max(...entries.map(([, count]) => count));
  return (
    <ul className="space-y-2.5">
      {entries.map(([label, count]) => (
        <li key={label} className="space-y-1">
          <div className="flex items-baseline justify-between gap-2 text-sm">
            <span className="min-w-0 truncate">{label}</span>
            <span className="font-mono tabular-nums text-muted-foreground">{count}</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-muted">
            <div
              className={cn("h-full rounded-full", barClassName)}
              style={{ width: `${max > 0 ? Math.max(4, (count / max) * 100) : 0}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}

function byCountDesc([, a]: [string, number], [, b]: [string, number]): number {
  return b - a;
}

export function AdminAnalyticsPage() {
  const query = useQuery({
    queryKey: ["admin-analytics"],
    queryFn: () => apiJson<AnalyticsSnapshot>("/api/v1/admin/analytics"),
  });

  const data = query.data;
  const totalRefusals = data ? sum(data.refusal_mix) : 0;
  const refusalRatePct = data && data.usage.total > 0
    ? Math.round((totalRefusals / data.usage.total) * 100)
    : null;
  const up = data?.feedback_trends.by_rating.up ?? 0;
  const down = data?.feedback_trends.by_rating.down ?? 0;
  const feedbackTotal = up + down;
  const helpfulPct = feedbackTotal > 0 ? Math.round((up / feedbackTotal) * 100) : null;

  return (
    <main className="mx-auto max-w-6xl space-y-6 px-6 py-10" data-testid="admin-metrics">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Metrics</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          What people are asking, whether they got an answer, and how they rated it.
        </p>
      </div>

      {query.isError ? (
        <p className="text-sm text-destructive" role="alert">
          Couldn't load metrics. You may not have admin access.
        </p>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4" data-testid="metrics-stat-tiles">
            {query.isLoading ? (
              Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-[86px]" />)
            ) : (
              <>
                <StatTile label="Chat requests" value={String(data?.usage.total ?? 0)} />
                <StatTile
                  label="p95 latency"
                  value={data && data.latency.samples > 0 ? `${Math.round(data.latency.p95_ms)} ms` : "Not available"}
                  hint={data && data.latency.samples > 0 ? `${data.latency.samples} sampled` : "No requests yet"}
                />
                <StatTile
                  label="Refusal rate"
                  value={refusalRatePct != null ? `${refusalRatePct}%` : "Not available"}
                  hint={`${totalRefusals} refused`}
                />
                <StatTile
                  label="Found helpful"
                  value={helpfulPct != null ? `${helpfulPct}%` : "Not available"}
                  hint={feedbackTotal > 0 ? `${up} up · ${down} down` : "No feedback yet"}
                />
              </>
            )}
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Refusal breakdown</CardTitle>
                <CardDescription>Why the system declined to answer.</CardDescription>
              </CardHeader>
              <CardContent>
                {query.isLoading ? (
                  <Skeleton className="h-24 w-full" />
                ) : (
                  <BarList
                    entries={Object.entries(data?.refusal_mix ?? {}).sort(byCountDesc)}
                    barClassName="bg-destructive"
                    emptyLabel="No refusals recorded."
                  />
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Feedback reasons</CardTitle>
                <CardDescription>Why people rated an answer down.</CardDescription>
              </CardHeader>
              <CardContent>
                {query.isLoading ? (
                  <Skeleton className="h-24 w-full" />
                ) : (
                  <BarList
                    entries={Object.entries(data?.feedback_trends.by_reason ?? {}).sort(byCountDesc)}
                    barClassName="bg-warning"
                    emptyLabel="No feedback recorded."
                  />
                )}
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Top unanswered questions</CardTitle>
              <CardDescription>
                What your documents are missing. A recurring one here is a candidate for a
                new upload or a broadened collection scope.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {query.isLoading ? (
                <Skeleton className="h-24 w-full" />
              ) : (data?.top_unanswered_questions.length ?? 0) === 0 ? (
                <EmptyState title="No unanswered questions yet." testId="metrics-no-unanswered" />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Question</TableHead>
                      <TableHead className="text-right">Times asked</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data?.top_unanswered_questions.map((row) => (
                      <TableRow key={row.question}>
                        <TableCell>{row.question}</TableCell>
                        <TableCell className="text-right font-mono tabular-nums">{row.count}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </main>
  );
}
