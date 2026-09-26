/**
 * @file EvidenceViewer.tsx
 * @description Shared "show me the source" modal — chat citations and document preview
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.1.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";

export function EvidenceViewer({
  open,
  onOpenChange,
  title,
  excerpt,
  note,
  testId = "evidence-viewer",
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  excerpt: string;
  /** Small disclaimer under the excerpt, e.g. "AI-generated interpretation" or a
   * best-effort-extraction warning. Omit for none. */
  note?: string;
  /** Prefix for data-testid on the excerpt/note nodes, so call sites keep stable ids. */
  testId?: string;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent data-testid={testId} aria-label={title || "Source viewer"}>
        <DialogTitle>{title || "Source"}</DialogTitle>
        <p
          data-testid={`${testId}-highlight`}
          className="max-h-[60vh] overflow-y-auto whitespace-pre-wrap rounded bg-warning/15 p-3 text-sm"
        >
          {excerpt || "No excerpt available"}
        </p>
        {note ? (
          <p data-testid={`${testId}-note`} className="text-xs text-muted-foreground">
            {note}
          </p>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
