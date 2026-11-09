import { describe, it, expect, vi } from "vitest";
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
  }),
  usePathname: () => "/",
}));
import { PermissionGate } from "@/components/integration/PermissionGate";
import { AccessDenied } from "@/components/integration/AccessDenied";
import { SessionExpired } from "@/components/integration/SessionExpired";
import { ConnectionStatus } from "@/components/integration/ConnectionStatus";

describe("Integration UI Components", () => {
  describe("PermissionGate", () => {
    it("renders children when required permission is present", () => {
      render(
        <PermissionGate granted={["documents.read", "analytics.read"]} required="analytics.read">
          <div data-testid="analytics-content">Analytics Dashboard</div>
        </PermissionGate>
      );
      expect(screen.getByTestId("analytics-content")).toBeInTheDocument();
    });

    it("renders fallback when required permission is missing", () => {
      render(
        <PermissionGate
          granted={["documents.read"]}
          required="developer.read"
          fallback={<div data-testid="fallback">Access Denied</div>}
        >
          <div>Developer Content</div>
        </PermissionGate>
      );
      expect(screen.getByTestId("fallback")).toBeInTheDocument();
      expect(screen.queryByText("Developer Content")).not.toBeInTheDocument();
    });
  });

  describe("AccessDenied", () => {
    it("renders accessible alert with permission guidance", () => {
      render(
        <AccessDenied
          requiredPermission="governance.review"
          resourceName="Review Management"
        />
      );
      expect(screen.getByRole("alert")).toBeInTheDocument();
      expect(screen.getByText(/governance.review/i)).toBeInTheDocument();
      expect(screen.getByText(/Review Management/i)).toBeInTheDocument();
    });

    it("calls onGoBack when back button is clicked", () => {
      const onGoBack = vi.fn();
      render(<AccessDenied onGoBack={onGoBack} />);
      const btn = screen.getByRole("button", { name: /go back/i });
      fireEvent.click(btn);
      expect(onGoBack).toHaveBeenCalledTimes(1);
    });
  });

  describe("SessionExpired", () => {
    it("renders accessible dialog and triggers refresh or sign-in", () => {
      const onRefresh = vi.fn();
      const onSignIn = vi.fn();

      render(
        <SessionExpired onRefresh={onRefresh} onSignIn={onSignIn} />
      );

      expect(screen.getByRole("dialog")).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: /session expired/i })).toBeInTheDocument();

      const refreshBtn = screen.getByRole("button", { name: /refresh session/i });
      fireEvent.click(refreshBtn);
      expect(onRefresh).toHaveBeenCalledTimes(1);

      const signInBtn = screen.getByRole("button", { name: /re-authenticate/i });
      fireEvent.click(signInBtn);
      expect(onSignIn).toHaveBeenCalledTimes(1);
    });
  });

  describe("ConnectionStatus", () => {
    it("renders status pill with accessible role and label", () => {
      const { rerender } = render(<ConnectionStatus status="connected" />);
      expect(screen.getByRole("status")).toHaveTextContent(/live synced/i);

      rerender(<ConnectionStatus status="reconnecting" />);
      expect(screen.getByRole("status")).toHaveTextContent(/reconnecting/i);

      const onRetry = vi.fn();
      rerender(<ConnectionStatus status="disconnected" onReconnect={onRetry} />);
      expect(screen.getByRole("status")).toHaveTextContent(/disconnected/i);

      const retryBtn = screen.getByRole("button", { name: /retry/i });
      fireEvent.click(retryBtn);
      expect(onRetry).toHaveBeenCalledTimes(1);
    });
  });
});
