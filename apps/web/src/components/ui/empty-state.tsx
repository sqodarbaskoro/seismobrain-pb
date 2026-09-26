/**
 * @file empty-state.tsx
 * @description Shared "nothing here yet" placeholder for lists and tables
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.1.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function EmptyState({
  title,
  action,
  testId,
  className,
}: {
  title: string;
  action?: ReactNode;
  testId?: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-md border border-dashed border-border px-4 py-8 text-center text-sm text-muted-foreground",
        className,
      )}
      data-testid={testId}
    >
      <p>{title}</p>
      {action ? <div className="mt-3">{action}</div> : null}
    </div>
  );
}
