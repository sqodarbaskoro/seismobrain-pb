/**
 * @file DocumentsPage.tsx
 * @description Collection browser: filters, upload, preview/download, bulk actions
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-18
 * @version 0.7.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
      author: doc.author ?? "",
 */

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, Eye, Pencil, Trash2 } from "lucide-react";
import {
  bulkAction,
  browseDocuments,
  downloadDocument,
  getIngestJobStatus,
  loadSampleDocuments,
  previewDocument,
  updateDocumentMetadata,
  uploadDocument,
  type DocumentFilters,
  type DocumentRow,
  type IngestJobStatus,
} from "@/api/services/documents";
import { createCollection, listMyWorkspaces, listWorkspaces } from "@/api/services/workspaces";
import { ApiError } from "@/api/client";
import { useSession } from "@/auth/session";
import { usePagination } from "@/lib/pagination";
import { sortByKey, type SortDirection } from "@/lib/sort";
import { cn } from "@/lib/utils";
import { EvidenceViewer } from "@/components/EvidenceViewer";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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

const EMPTY_FILTERS: DocumentFilters = {};

/** Real pipeline stages a job passes through, in order — QUEUED/STARTING come before
 * any of the three that matter to a person watching an upload; READY is "done". */
const STAGE_SEQUENCE = ["QUEUED", "STARTING", "PARSED", "CHUNKED", "INDEXED", "READY"];
const STAGE_LABELS: Record<string, string> = {
  QUEUED: "Queued",
  STARTING: "Starting",
  PARSED: "Parsed",
  CHUNKED: "Chunked",
  INDEXED: "Indexed",
  READY: "Ready",
};
const FAILED_JOB_STATUSES = new Set(["failed", "dead_letter", "quarantined"]);

type TrackedJob = { jobId: string; filename: string };

function IngestProgressRow({ filename, status }: { filename: string; status?: IngestJobStatus }) {
  const stage = status?.stage ?? "QUEUED";
  const stepIndex = Math.max(0, STAGE_SEQUENCE.indexOf(stage));
  const pct = Math.round((stepIndex / (STAGE_SEQUENCE.length - 1)) * 100);
  const failed = Boolean(status && FAILED_JOB_STATUSES.has(status.status));
  return (
    <li
      className="space-y-1.5 rounded-md border border-border bg-card p-2.5 text-sm"
      data-testid="ingest-progress-row"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="min-w-0 truncate font-medium" title={filename}>{filename}</span>
        <span className={cn("font-mono text-xs", failed ? "text-destructive" : "text-muted-foreground")}>
          {failed ? "Failed" : STAGE_LABELS[stage] ?? stage}
        </span>
      </div>
      {failed ? (
        <p className="text-xs text-destructive">{status?.error ?? "Processing failed."}</p>
      ) : (
        <div className="h-1.5 overflow-hidden rounded-full bg-muted">
          <div className="h-full rounded-full bg-cited transition-all" style={{ width: `${pct}%` }} />
        </div>
      )}
    </li>
  );
}

export function DocumentsPage() {
  const user = useSession((s) => s.user);
  const isAdmin = user?.system_role === "system_admin";
  const queryClient = useQueryClient();

  const [collectionId, setCollectionId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [uploadBusy, setUploadBusy] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string | null>(null);
  const [sampleBusy, setSampleBusy] = useState(false);
  const [uploadJobs, setUploadJobs] = useState<TrackedJob[]>([]);
  const [jobStatuses, setJobStatuses] = useState<Record<string, IngestJobStatus>>({});
  const uploadJobsRef = useRef<TrackedJob[]>([]);
  useEffect(() => {
    uploadJobsRef.current = uploadJobs;
  }, [uploadJobs]);

  const [filters, setFilters] = useState<DocumentFilters>(EMPTY_FILTERS);
  const [showMoreFilters, setShowMoreFilters] = useState(false);

  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewTitle, setPreviewTitle] = useState("");
  const [previewText, setPreviewText] = useState("");
  const [previewNote, setPreviewNote] = useState<string | undefined>();

  const [editingDoc, setEditingDoc] = useState<DocumentRow | null>(null);
  const [editFields, setEditFields] = useState<Record<string, string>>({});
  const [editBusy, setEditBusy] = useState(false);

  const [newCollectionOpen, setNewCollectionOpen] = useState(false);
  const [newCollectionName, setNewCollectionName] = useState("");
  const [newCollectionWorkspaceId, setNewCollectionWorkspaceId] = useState("");

  const [moveTargetId, setMoveTargetId] = useState("");
  const [tagInput, setTagInput] = useState("");
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);

  const collectionsQuery = useQuery({ queryKey: ["my-workspaces"], queryFn: listMyWorkspaces });
  const collectionOptions = useMemo(
    () => (collectionsQuery.data?.workspaces ?? []).flatMap((w) => w.collections),
    [collectionsQuery.data],
  );
  const collections = useMemo(() => collectionOptions.map((c) => c.id), [collectionOptions]);

  useEffect(() => {
    const first = collections[0];
    if (first && !collectionId) setCollectionId(first);
  }, [collections, collectionId]);

  const workspacesQuery = useQuery({
    queryKey: ["admin-workspaces-for-picker"],
    queryFn: listWorkspaces,
    enabled: isAdmin && newCollectionOpen,
  });

  const docsQuery = useQuery({
    queryKey: ["documents", collectionId, filters],
    enabled: Boolean(collectionId),
    queryFn: () => browseDocuments(collectionId, filters),
  });
  const documents = docsQuery.data?.documents ?? [];

  // Poll each tracked upload's real ingest stage rather than blindly re-fetching the
  // document list on a timer — the list only needs refreshing once a job actually
  // reaches "succeeded" (at which point the document is already visible server-side).
  useEffect(() => {
    if (!collectionId) return;
    let cancelled = false;
    const timer = setInterval(() => {
      void (async () => {
        const jobs = uploadJobsRef.current;
        if (jobs.length === 0) return;
        const results = await Promise.all(
          jobs.map(async ({ jobId }) => {
            try {
              return [jobId, await getIngestJobStatus(collectionId, jobId)] as const;
            } catch {
              return null;
            }
          }),
        );
        if (cancelled) return;
        const next: Record<string, IngestJobStatus> = {};
        let anySucceeded = false;
        for (const entry of results) {
          if (!entry) continue;
          const [jobId, status] = entry;
          next[jobId] = status;
          if (status.status === "succeeded") anySucceeded = true;
        }
        if (Object.keys(next).length === 0) return;
        setJobStatuses((prev) => ({ ...prev, ...next }));
        setUploadJobs((prev) => prev.filter(({ jobId }) => next[jobId]?.status !== "succeeded"));
        if (anySucceeded) {
          void queryClient.invalidateQueries({ queryKey: ["documents", collectionId] });
        }
      })();
    }, 1200);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [collectionId, queryClient]);
  const [sortKey, setSortKey] = useState<"title" | "doc_type">("title");
  const [sortDir, setSortDir] = useState<SortDirection>("asc");
  const sortedDocuments = useMemo(() => {
    const keyFn: (d: DocumentRow) => string =
      sortKey === "title" ? (d) => (d.title || d.id).toLowerCase() : (d) => (d.doc_type || "").toLowerCase();
    return sortByKey(documents, keyFn, sortDir);
  }, [documents, sortKey, sortDir]);
  const { page, setPage, totalPages, pageItems } = usePagination(sortedDocuments, 20);

  function toggleDocSort(key: "title" | "doc_type") {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

  useEffect(() => {
    setSelected(new Set());
  }, [collectionId]);

  function setFilter(key: keyof DocumentFilters, value: string) {
    setFilters((prev) => ({ ...prev, [key]: value || undefined }));
  }

  const activeFilterCount = useMemo(
    () => Object.values(filters).filter(Boolean).length,
    [filters],
  );

  async function onUpload(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!collectionId) return;
    const form = e.currentTarget;
    const fileInput = form.elements.namedItem("file") as HTMLInputElement;
    const files = fileInput.files ? Array.from(fileInput.files) : [];
    if (files.length === 0) {
      setError("Choose at least one file to upload");
      return;
    }
    setError(null);
    setUploadBusy(true);
    const failures: string[] = [];
    let successCount = 0;
    const newJobs: TrackedJob[] = [];
    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i]!;
        setUploadProgress(`Uploading ${i + 1} of ${files.length}…`);
        try {
          const result = await uploadDocument(collectionId, file);
          newJobs.push({ jobId: result.job_id, filename: file.name });
          successCount += 1;
        } catch (err) {
          const reason =
            err instanceof ApiError
              ? err.status === 403
                ? "permission denied"
                : err.detail
              : "upload failed";
          failures.push(`${file.name}: ${reason}`);
        }
      }
      if (newJobs.length > 0) setUploadJobs((prev) => [...prev, ...newJobs]);
      form.reset();
      if (failures.length === 0) {
        toast.success(
          successCount === 1
            ? `Uploading "${files[0]!.name}". It'll appear below once processed.`
            : `Uploading ${successCount} files. They'll appear below once processed.`,
        );
      } else if (successCount > 0) {
        setError(`${failures.length} of ${files.length} failed: ${failures.join("; ")}`);
        toast.success(`Uploaded ${successCount} of ${files.length} files.`);
      } else {
        const allForbidden = failures.every((f) => f.includes("permission denied"));
        setError(
          allForbidden
            ? "You don't have permission to add documents to this collection. Ask an admin."
            : `Upload failed: ${failures.join("; ")}`,
        );
      }
    } finally {
      setUploadBusy(false);
      setUploadProgress(null);
    }
  }

  async function onLoadSamples() {
    if (!collectionId) return;
    setError(null);
    setSampleBusy(true);
    try {
      const result = await loadSampleDocuments(collectionId);
      setUploadJobs((prev) => [
        ...prev,
        ...result.documents.map((d) => ({ jobId: d.job_id, filename: "Sample document" })),
      ]);
      toast.success(`Added ${result.documents.length} sample document(s).`);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.status === 403
            ? "Loading sample documents is an admin action."
            : err.detail
          : "Couldn't load sample documents",
      );
    } finally {
      setSampleBusy(false);
    }
  }

  async function onPreview(documentId: string) {
    setError(null);
    try {
      const result = await previewDocument(documentId);
      setPreviewTitle(result.title || documentId);
      setPreviewText(result.text);
      setPreviewNote(
        result.best_effort
          ? "Best-effort byte decode. This format isn't fully parsed, so the text may look garbled."
          : result.truncated
            ? "Showing the first part of this document."
            : undefined,
      );
      setPreviewOpen(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Couldn't open preview");
    }
  }

  function onEditOpen(doc: DocumentRow) {
    setEditingDoc(doc);
    setEditFields({
      title: doc.title ?? "",
      doc_type: doc.doc_type ?? "",
      revision: doc.revision ?? "",
      effective_date: doc.effective_date ?? "",
      language: doc.language ?? "",
    });
  }

  async function onSaveMetadata() {
    if (!editingDoc) return;
    setError(null);
    setEditBusy(true);
    try {
      await updateDocumentMetadata(editingDoc.id, editFields);
      await queryClient.invalidateQueries({ queryKey: ["documents", collectionId] });
      setEditingDoc(null);
      toast.success("Metadata updated.");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Couldn't save metadata");
    } finally {
      setEditBusy(false);
    }
  }

  async function onDownload(documentId: string) {
    setError(null);
    try {
      const { blob, filename } = await downloadDocument(documentId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Download failed");
    }
  }

  const bulk = useMutation({
    mutationFn: bulkAction,
    onSuccess: async (result) => {
      toast.success(`${result.action === "delete" ? "Deleted" : "Updated"} ${result.count} document(s).`);
      setSelected(new Set());
      setDeleteConfirmOpen(false);
      setMoveTargetId("");
      setTagInput("");
      await queryClient.invalidateQueries({ queryKey: ["documents", collectionId] });
    },
    onError: (err) => {
      setError(err instanceof ApiError ? err.detail : "That bulk action failed");
    },
  });

  function toggleSelected(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function onCreateCollection() {
    setError(null);
    try {
      const created = await createCollection(newCollectionWorkspaceId, newCollectionName.trim());
      await collectionsQuery.refetch();
      setCollectionId(created.id);
      setNewCollectionOpen(false);
      setNewCollectionName("");
      toast.success(`Created collection "${created.name}".`);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Couldn't create the collection");
    }
  }

  return (
    <main className="mx-auto max-w-5xl space-y-6 px-6 py-10" data-testid="documents-page">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-3xl font-semibold tracking-tight">Documents</h1>
        {isAdmin ? (
          <Button variant="outline" size="sm" onClick={() => setNewCollectionOpen(true)}>
            + New collection
          </Button>
        ) : null}
      </div>

      {error ? (
        <p role="alert" className="text-sm text-destructive" data-testid="documents-error">
          {error}
        </p>
      ) : null}

      <section className="space-y-2" aria-label="Collection picker">
        <Label htmlFor="collection">Collection</Label>
        <Select value={collectionId} onValueChange={setCollectionId}>
          <SelectTrigger id="collection" className="max-w-md" aria-label="Collection">
            <SelectValue placeholder="Choose a collection" />
          </SelectTrigger>
          <SelectContent>
            {collectionOptions.map((c) => (
              <SelectItem key={c.id} value={c.id}>
                {c.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {!collectionsQuery.isLoading && collections.length === 0 ? (
          <EmptyState
            title={`No collections yet. ${
              isAdmin ? "Create one above, or run guided setup." : "Ask an admin to add you to one."
            }`}
          />
        ) : null}
      </section>

      <section className="space-y-3" aria-label="Search and filter">
        <div className="flex flex-wrap items-center gap-2">
          <Input
            className="max-w-sm"
            placeholder="Search by title…"
            aria-label="Search documents"
            value={filters.q ?? ""}
            onChange={(e) => setFilter("q", e.target.value)}
          />
          <Button variant="ghost" size="sm" onClick={() => setShowMoreFilters((v) => !v)}>
            {showMoreFilters ? "Fewer filters" : "More filters"}
            {activeFilterCount > 0 ? ` (${activeFilterCount})` : ""}
          </Button>
          {activeFilterCount > 0 ? (
            <Button variant="ghost" size="sm" onClick={() => setFilters(EMPTY_FILTERS)}>
              Clear
            </Button>
          ) : null}
        </div>
        {showMoreFilters ? (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {(
              [
                ["doc_type", "File type"],
                ["tag", "Tag"],
                ["revision", "Revision"],
                ["effective_date", "Effective date"],
                ["author", "Author"],
                ["language", "Language"],
              ] as const
            ).map(([key, label]) => (
              <div key={key} className="space-y-1">
                <Label htmlFor={`filter-${key}`} className="text-xs text-muted-foreground">
                  {label}
                </Label>
                <Input
                  id={`filter-${key}`}
                  value={filters[key] ?? ""}
                  onChange={(e) => setFilter(key, e.target.value)}
                />
              </div>
            ))}
          </div>
        ) : null}
      </section>

      <section aria-label="Add documents">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Add documents</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap items-center gap-3">
            <form className="flex flex-wrap items-center gap-2" onSubmit={onUpload}>
              <input
                id="file"
                name="file"
                type="file"
                multiple
                accept=".pdf,.md,.txt,.docx"
                className="text-sm"
              />
              <Button type="submit" variant="outline" size="sm" disabled={!collectionId || uploadBusy}>
                {uploadBusy ? (uploadProgress ?? "Uploading…") : "Upload"}
              </Button>
            </form>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              disabled={!collectionId || sampleBusy}
              onClick={() => void onLoadSamples()}
            >
              {sampleBusy ? "Loading…" : "Load sample documents"}
            </Button>
          </CardContent>
          {uploadJobs.length > 0 ? (
            <CardContent className="pt-0">
              <ul className="space-y-2" data-testid="ingest-progress-list" aria-label="Processing uploads">
                {uploadJobs.map(({ jobId, filename }) => (
                  <IngestProgressRow key={jobId} filename={filename} status={jobStatuses[jobId]} />
                ))}
              </ul>
            </CardContent>
          ) : null}
        </Card>
      </section>

      {selected.size > 0 ? (
        <section
          className="flex flex-wrap items-center gap-3 rounded-md border border-primary/30 bg-primary/5 p-3"
          aria-label="Bulk actions"
          data-testid="bulk-toolbar"
        >
          <span className="text-sm font-medium">{selected.size} selected</span>
          <Select value={moveTargetId} onValueChange={setMoveTargetId}>
            <SelectTrigger className="h-8 w-40" aria-label="Move to collection">
              <SelectValue placeholder="Move to…" />
            </SelectTrigger>
            <SelectContent>
              {collectionOptions.filter((c) => c.id !== collectionId).map((c) => (
                <SelectItem key={c.id} value={c.id}>
                  {c.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            size="sm"
            variant="outline"
            disabled={!moveTargetId || bulk.isPending}
            onClick={() =>
              bulk.mutate({
                document_ids: [...selected],
                action: "move",
                target_collection_id: moveTargetId,
              })
            }
          >
            Move
          </Button>
          <Input
            className="h-8 w-32"
            placeholder="Add tag…"
            aria-label="Tag to apply"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
          />
          <Button
            size="sm"
            variant="outline"
            disabled={!tagInput.trim() || bulk.isPending}
            onClick={() =>
              bulk.mutate({ document_ids: [...selected], action: "retag", tags: [tagInput.trim()] })
            }
          >
            Apply tag
          </Button>
          <Button
            size="sm"
            variant="destructive"
            disabled={bulk.isPending}
            onClick={() => setDeleteConfirmOpen(true)}
          >
            <Trash2 className="h-4 w-4" aria-hidden="true" />
            Delete
          </Button>
        </section>
      ) : null}

      <section className="space-y-2" aria-label="Document list">
        {/* Below md: stacked cards instead of a horizontally-scrolling table. */}
        <div className="space-y-3 md:hidden">
          {docsQuery.isLoading
            ? Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-28 w-full" />)
            : pageItems.map((doc) => (
                <Card key={doc.id} className="p-4">
                  <div className="flex items-start gap-3">
                    <input
                      type="checkbox"
                      aria-label={`Select ${doc.title || doc.id}`}
                      checked={selected.has(doc.id)}
                      onChange={() => toggleSelected(doc.id)}
                      className="mt-1"
                    />
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-medium">{doc.title || doc.id}</p>
                      <p className="text-sm text-muted-foreground">{doc.doc_type}</p>
                      {(doc.tags ?? []).length > 0 ? (
                        <div className="mt-1">
                          {(doc.tags ?? []).map((t) => (
                            <Badge key={t} variant="secondary" className="mr-1">
                              {t}
                            </Badge>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <Button variant="ghost" size="sm" onClick={() => void onPreview(doc.id)}>
                      <Eye className="h-4 w-4" aria-hidden="true" />
                      Preview
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => void onDownload(doc.id)}>
                      <Download className="h-4 w-4" aria-hidden="true" />
                      Download
                    </Button>
                    {isAdmin ? (
                      <Button variant="ghost" size="sm" onClick={() => onEditOpen(doc)}>
                        <Pencil className="h-4 w-4" aria-hidden="true" />
                        Edit
                      </Button>
                    ) : null}
                  </div>
                </Card>
              ))}
        </div>

        <div className="hidden md:block">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-8">
                <span className="sr-only">Select</span>
              </TableHead>
              <TableHead>
                <SortButton
                  label="Title"
                  active={sortKey === "title"}
                  direction={sortDir}
                  onClick={() => toggleDocSort("title")}
                />
              </TableHead>
              <TableHead>
                <SortButton
                  label="Type"
                  active={sortKey === "doc_type"}
                  direction={sortDir}
                  onClick={() => toggleDocSort("doc_type")}
                />
              </TableHead>
              <TableHead>Tags</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {docsQuery.isLoading
              ? Array.from({ length: 4 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell colSpan={5}>
                      <Skeleton className="h-8 w-full" />
                    </TableCell>
                  </TableRow>
                ))
              : pageItems.map((doc) => (
              <TableRow key={doc.id} data-testid="document-row">
                <TableCell>
                  <input
                    type="checkbox"
                    aria-label={`Select ${doc.title || doc.id}`}
                    checked={selected.has(doc.id)}
                    onChange={() => toggleSelected(doc.id)}
                  />
                </TableCell>
                <TableCell className="font-medium">{doc.title || doc.id}</TableCell>
                <TableCell className="text-muted-foreground">{doc.doc_type}</TableCell>
                <TableCell>
                  {(doc.tags ?? []).map((t) => (
                    <Badge key={t} variant="secondary" className="mr-1">
                      {t}
                    </Badge>
                  ))}
                </TableCell>
                <TableCell className="text-right">
                  <Button variant="ghost" size="sm" onClick={() => void onPreview(doc.id)}>
                    <Eye className="h-4 w-4" aria-hidden="true" />
                    Preview
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => void onDownload(doc.id)}>
                    <Download className="h-4 w-4" aria-hidden="true" />
                    Download
                  </Button>
                  {isAdmin ? (
                    <Button variant="ghost" size="sm" onClick={() => onEditOpen(doc)}>
                      <Pencil className="h-4 w-4" aria-hidden="true" />
                      Edit
                    </Button>
                  ) : null}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        </div>
        {!docsQuery.isLoading && documents.length === 0 ? (
          <EmptyState
            title={
              activeFilterCount > 0
                ? "No documents match these filters."
                : "No documents in this collection yet. Add one above."
            }
          />
        ) : null}
        <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
      </section>

      <EvidenceViewer
        open={previewOpen}
        onOpenChange={setPreviewOpen}
        title={previewTitle}
        excerpt={previewText}
        note={previewNote}
        testId="document-preview"
      />

      <Dialog open={editingDoc != null} onOpenChange={(open) => !open && setEditingDoc(null)}>
        <DialogContent data-testid="edit-metadata-dialog">
          <DialogHeader>
            <DialogTitle>Edit metadata</DialogTitle>
            <DialogDescription>
              Correct what was auto-extracted at upload. This is useful when a title or date came
              through wrong.
            </DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-3">
            {(
              [
                ["title", "Title"],
                ["doc_type", "File type"],
                ["revision", "Revision"],
                ["effective_date", "Effective date"],
                ["author", "Author"],
                ["language", "Language"],
              ] as const
            ).map(([key, label]) => (
              <div key={key} className="space-y-1">
                <Label htmlFor={`edit-${key}`}>{label}</Label>
                <Input
                  id={`edit-${key}`}
                  value={editFields[key] ?? ""}
                  onChange={(e) => setEditFields((prev) => ({ ...prev, [key]: e.target.value }))}
                />
              </div>
            ))}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingDoc(null)}>
              Cancel
            </Button>
            <Button disabled={editBusy} onClick={() => void onSaveMetadata()}>
              {editBusy ? "Saving…" : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={newCollectionOpen} onOpenChange={setNewCollectionOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New collection</DialogTitle>
            <DialogDescription>A collection is a folder of documents inside a workspace.</DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="new-col-ws">Workspace</Label>
              <Select value={newCollectionWorkspaceId} onValueChange={setNewCollectionWorkspaceId}>
                <SelectTrigger id="new-col-ws">
                  <SelectValue placeholder="Choose a workspace" />
                </SelectTrigger>
                <SelectContent>
                  {(workspacesQuery.data?.workspaces ?? []).map((ws) => (
                    <SelectItem key={ws.id} value={ws.id}>
                      {ws.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="new-col-name">Name</Label>
              <Input
                id="new-col-name"
                value={newCollectionName}
                onChange={(e) => setNewCollectionName(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              disabled={!newCollectionWorkspaceId || !newCollectionName.trim()}
              onClick={() => void onCreateCollection()}
            >
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete {selected.size} document(s)?</DialogTitle>
            <DialogDescription>
              This removes them from search and browsing. This can't be undone from here.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteConfirmOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              disabled={bulk.isPending}
              onClick={() => bulk.mutate({ document_ids: [...selected], action: "delete" })}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </main>
  );
}
