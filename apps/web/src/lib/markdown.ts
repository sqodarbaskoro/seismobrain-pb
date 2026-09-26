/**
 * @file markdown.ts
 * @description Sanitize Markdown for chat rendering; never allow raw HTML (SEC-09)
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-16
 * @modified 2026-09-18
 * @version 0.1.1
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

const HTML_TAG = /<\/?[a-z][^>]*>/gi;
const SCRIPTISH = /javascript:/gi;

/**
 * Strip HTML tags for safe React text rendering.
 * Do not HTML-entity-encode: callers put the result in React text nodes, which
 * already escape; encoding would show literal &quot; / &amp; to the user.
 */
export function sanitizeMarkdown(input: string): string {
  return input.replace(HTML_TAG, "").replace(SCRIPTISH, "");
}

export function containsRawHtml(input: string): boolean {
  return /<[a-z][\s\S]*>/i.test(input);
}
