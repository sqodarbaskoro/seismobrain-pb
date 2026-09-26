/**
 * @file RequireAuth.test.tsx
 * @description Role gating: admin-only routes render for admins, block members
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.1.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it } from "vitest";
import { RequireAuth } from "@/auth/RequireAuth";
import { useSession } from "@/auth/session";

function renderGated() {
  return render(
    <MemoryRouter initialEntries={["/admin/users"]}>
      <RequireAuth role="system_admin">
        <div data-testid="protected-content">Admin area</div>
      </RequireAuth>
    </MemoryRouter>,
  );
}

describe("RequireAuth role gating", () => {
  beforeEach(() => {
    useSession.setState({ accessToken: null, csrfToken: null, user: null });
  });

  it("renders protected content for a system_admin user", () => {
    useSession.setState({
      accessToken: "token",
      user: { id: "1", email: "admin@example.com", name: "Admin", system_role: "system_admin" },
    });
    renderGated();
    expect(screen.getByTestId("protected-content")).toBeInTheDocument();
  });

  it("shows an access-denied message for a non-admin user instead of the page", () => {
    useSession.setState({
      accessToken: "token",
      user: { id: "2", email: "member@example.com", name: "Member", system_role: "user" },
    });
    renderGated();
    expect(screen.getByTestId("access-denied")).toBeInTheDocument();
    expect(screen.queryByTestId("protected-content")).not.toBeInTheDocument();
  });
});
