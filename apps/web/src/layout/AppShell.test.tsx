/**
 * @file AppShell.test.tsx
 * @description Mobile nav collapse and app-wide theme toggle in the authenticated chrome
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.1.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it } from "vitest";
import { useSession } from "@/auth/session";
import { AppShell } from "@/layout/AppShell";
import { ThemeProvider } from "@/lib/theme";

beforeEach(() => {
  useSession.setState({
    user: { id: "u1", email: "admin@example.com", name: "Admin", system_role: "system_admin" },
  });
  document.documentElement.classList.remove("dark");
  window.localStorage.clear();
});

function renderShell() {
  return render(
    <ThemeProvider>
      <MemoryRouter initialEntries={["/chat"]}>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/chat" element={<div>chat</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("AppShell", () => {
  it("mobile nav toggle expands and collapses the nav panel", () => {
    renderShell();
    const toggle = screen.getByRole("button", { name: "Open menu" });
    expect(toggle).toHaveAttribute("aria-expanded", "false");

    fireEvent.click(toggle);
    expect(screen.getByRole("button", { name: "Close menu" })).toHaveAttribute(
      "aria-expanded",
      "true",
    );
  });

  it("theme toggle flips the global .dark class", () => {
    renderShell();
    expect(document.documentElement.classList.contains("dark")).toBe(false);

    fireEvent.click(screen.getByRole("button", { name: "Toggle theme" }));
    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });
});
