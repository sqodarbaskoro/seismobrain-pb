/**
 * @file QuarantinePage.tsx
 * @description Files needing review — release items held back from ingestion
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.2.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { listQuarantine, releaseQuarantineItem } from "@/api/services/quarantine";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { toast } from "@/components/ui/sonner";

export function QuarantinePage() {
  const queryClient = useQueryClient();
  const itemsQuery = useQuery({ queryKey: ["quarantine"], queryFn: listQuarantine });
  const items = itemsQuery.data?.items ?? [];

  const release = useMutation({
    mutationFn: releaseQuarantineItem,
    onSuccess: async () => {
      toast.success("Released. It can now continue processing.");
      await queryClient.invalidateQueries({ queryKey: ["quarantine"] });
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.detail : "Couldn't release that file");
    },
  });

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-6 py-10" data-testid="quarantine-page">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Files needing review</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Uploads held back because of a failed check or something a curator flagged.
          Nothing gets held back automatically yet in this release; this list only fills up
          if something is explicitly flagged.
        </p>
      </div>

      {itemsQuery.isError ? (
        <p role="alert" className="text-sm text-destructive">
          Couldn't load the review list. You may not have admin access.
        </p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>File</TableHead>
              <TableHead>Reason</TableHead>
              <TableHead className="text-right">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {itemsQuery.isLoading
              ? Array.from({ length: 3 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell colSpan={3}>
                      <Skeleton className="h-8 w-full" />
                    </TableCell>
                  </TableRow>
                ))
              : items.map((item) => (
              <TableRow key={item.id} data-testid="quarantine-row">
                <TableCell className="font-medium">{item.filename}</TableCell>
                <TableCell className="text-muted-foreground">{item.reason}</TableCell>
                <TableCell className="text-right">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={release.isPending}
                    onClick={() => release.mutate(item.id)}
                  >
                    Release
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
      {!itemsQuery.isLoading && !itemsQuery.isError && items.length === 0 ? (
        <EmptyState title="Nothing is waiting for review right now." />
      ) : null}
    </main>
  );
}
