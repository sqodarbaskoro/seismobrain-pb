/**
 * @file sort.ts
 * @description Client-side single-column sort over an already-loaded array
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.1.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

export type SortDirection = "asc" | "desc";

export function sortByKey<T>(
  items: T[],
  key: (item: T) => string | number,
  direction: SortDirection,
): T[] {
  const sorted = [...items].sort((a, b) => {
    const av = key(a);
    const bv = key(b);
    if (av < bv) return -1;
    if (av > bv) return 1;
    return 0;
  });
  return direction === "asc" ? sorted : sorted.reverse();
}
