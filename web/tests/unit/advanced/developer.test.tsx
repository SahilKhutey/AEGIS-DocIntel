import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { isSafeWebhookUrl } from "@/features/developer/schemas/developer.schema";
import { ApiCredentialManager } from "@/features/developer/components/ApiCredentialManager";
import { WebhookManager } from "@/features/developer/components/WebhookManager";
import { ApiExplorer } from "@/features/developer/components/ApiExplorer";

describe("Developer Interface components & SSRF validation", () => {
  describe("SSRF Protection (isSafeWebhookUrl)", () => {
    it("allows valid public HTTPS endpoints", () => {
      expect(isSafeWebhookUrl("https://api.github.com/webhook")).toBe(true);
      expect(isSafeWebhookUrl("https://events.enterprise.com/ingest")).toBe(true);
      expect(isSafeWebhookUrl("http://public-webhook-receiver.org/hook")).toBe(true);
    });

    it("rejects localhost and loopback domains", () => {
      expect(isSafeWebhookUrl("http://localhost:8000/webhook")).toBe(false);
      expect(isSafeWebhookUrl("http://127.0.0.1:8000/hook")).toBe(false);
      expect(isSafeWebhookUrl("http://0.0.0.0/")).toBe(false);
      expect(isSafeWebhookUrl("http://app.localhost/hook")).toBe(false);
    });

    it("rejects private RFC1918 subnets", () => {
      expect(isSafeWebhookUrl("http://10.0.0.1/admin")).toBe(false);
      expect(isSafeWebhookUrl("http://192.168.1.100/internal")).toBe(false);
      expect(isSafeWebhookUrl("http://172.16.0.5/api")).toBe(false);
      expect(isSafeWebhookUrl("http://172.31.255.255/hook")).toBe(false);
    });

    it("rejects AWS/GCP cloud metadata IP", () => {
      expect(isSafeWebhookUrl("http://169.254.169.254/latest/meta-data")).toBe(false);
      expect(isSafeWebhookUrl("http://metadata.google.internal/computeMetadata")).toBe(false);
    });
  });

  describe("ApiCredentialManager", () => {
    it("renders existing keys and handles new key generation modal", async () => {
      render(<ApiCredentialManager />);
      await waitFor(() => {
        expect(screen.getByText("Production Ingestion Pipeline")).toBeInTheDocument();
      });

      const genBtn = screen.getByRole("button", { name: /Generate API Key/i });
      fireEvent.click(genBtn);

      expect(screen.getByText("Provision New API Key")).toBeInTheDocument();
      expect(screen.getByLabelText(/Key Identifier/i)).toBeInTheDocument();
    });
  });

  describe("WebhookManager", () => {
    it("renders webhook endpoints and delivery logs", async () => {
      render(<WebhookManager />);
      await waitFor(() => {
        expect(screen.getByText("Webhook Subscriptions")).toBeInTheDocument();
        expect(screen.getByText("Recent Webhook Deliveries")).toBeInTheDocument();
      });
    });
  });

  describe("ApiExplorer", () => {
    it("renders endpoints and switches code snippet language", () => {
      render(<ApiExplorer />);
      expect(screen.getAllByText("/v1/admin/stats").length).toBeGreaterThan(0);
      expect(screen.getByText(/Retrieve tenant statistics/i)).toBeInTheDocument();

      const pythonBtn = screen.getByRole("button", { name: /Python/i });
      fireEvent.click(pythonBtn);
      expect(screen.getByText(/import requests/i)).toBeInTheDocument();
    });
  });
});
