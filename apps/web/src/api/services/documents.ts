/**
 * @file documents.ts
 * @description Typed calls for the documents domain: browse, upload, preview, download, bulk
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.1.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { ApiError, apiFetch, apiJson } from "@/api/client";

export type DocumentRow = {
  id: string;
  collection_id: string;
  title: string;
  doc_type: string;
  revision: string;
  effective_date: string;
  author: string;
  language: string;
  tags: string[];
  tag: string;
};

export type DocumentFilters = {
  q?: string;
  doc_type?: string;
  tag?: string;
  revision?: string;
  effective_date?: string;
  author?: string;
  language?: string;
};

export type PreviewResult = {
  id: string;
  title: string;
  doc_type: string;
  text: string;
  truncated: boolean;
  best_effort: boolean;
};

export type BulkActionKind = "move" | "retag" | "delete" | "reindex";

function query(filters: DocumentFilters): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value) params.set(key, value);
  }
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export function listCollections(): Promise<{ collections: string[] }> {
  return apiJson("/api/v1/collections");
}

export function browseDocuments(
  collectionId: string,
  filters: DocumentFilters = {},
): Promise<{ documents: DocumentRow[] }> {
  return apiJson(
    `/api/v1/collections/${encodeURIComponent(collectionId)}/documents${query(filters)}`,
  );
}

export function uploadDocument(
  collectionId: string,
  file: File,
): Promise<{ document_id: string; job_id: string; object_key: string }> {
  const body = new FormData();
  body.append("file", file);
  return apiJson(`/api/v1/collections/${encodeURIComponent(collectionId)}/documents`, {
    method: "POST",
    body,
  });
}

export type IngestJobStatus = {
  id: string;
  stage: string;
  status: "pending" | "running" | "succeeded" | "failed" | "dead_letter" | "quarantined";
  error: string | null;
};

export function getIngestJobStatus(
  collectionId: string,
  jobId: string,
): Promise<IngestJobStatus> {
  return apiJson(
    `/api/v1/collections/${encodeURIComponent(collectionId)}/jobs/${encodeURIComponent(jobId)}`,
  );
}

export function previewDocument(documentId: string): Promise<PreviewResult> {
  return apiJson(`/documents/${encodeURIComponent(documentId)}/preview`);
}

/** Downloads real bytes (auth needs a bearer header, so a plain <a href> can't be used). */
export async function downloadDocument(
  documentId: string,
): Promise<{ blob: Blob; filename: string }> {
  const res = await apiFetch(`/documents/${encodeURIComponent(documentId)}/download`);
  if (!res.ok) throw new ApiError(res.status, await res.text());
  const disposition = res.headers.get("Content-Disposition") || "";
  const match = /filename="([^"]+)"/.exec(disposition);
  return { blob: await res.blob(), filename: match?.[1] || documentId };
}

export function bulkAction(body: {
  document_ids: string[];
  action: BulkActionKind;
  target_collection_id?: string;
  tags?: string[];
}): Promise<{ action: string; count: number }> {
  return apiJson("/api/v1/documents/bulk", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function loadSampleDocuments(
  collectionId: string,
): Promise<{ documents: { document_id: string; job_id: string }[] }> {
  return apiJson(`/api/v1/collections/${encodeURIComponent(collectionId)}/sample-documents`, {
    method: "POST",
  });
}

export function updateDocumentMetadata(
  documentId: string,
  fields: Record<string, string>,
): Promise<{ document_id: string; fields: Record<string, string> }> {
  return apiJson("/api/v1/metadata/review", {
    method: "POST",
    body: JSON.stringify({ document_id: documentId, fields }),
  });
}
