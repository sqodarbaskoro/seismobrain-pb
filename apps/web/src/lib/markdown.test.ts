/**
 * @file markdown.test.ts
 * @description Markdown sanitization never renders raw HTML (T3.11)
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-16
 * @modified 2026-09-18
 * @version 0.1.1
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { describe, expect, it } from "vitest";
import { containsRawHtml, sanitizeMarkdown } from "./markdown";

describe("sanitizeMarkdown", () => {
  it("strips raw HTML so it cannot render", () => {
    const dirty = 'Hello <script>alert(1)</script> <b>world</b>';
    const clean = sanitizeMarkdown(dirty);
    expect(clean).not.toContain("<script>");
    expect(clean).not.toContain("<b>");
    expect(containsRawHtml(clean)).toBe(false);
    expect(clean).toContain("Hello");
    expect(clean).toContain("world");
  });

  it("preserves plain text content", () => {
    expect(sanitizeMarkdown("Torque is 40 Nm [E1]")).toContain("Torque is 40 Nm");
  });

  it("keeps quotation marks readable (no &quot; entities)", () => {
    expect(sanitizeMarkdown('"SP unsync"')).toBe('"SP unsync"');
    expect(sanitizeMarkdown("it's fine")).toBe("it's fine");
  });
});
