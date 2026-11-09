import { describe, it, expect, vi } from "vitest";
import { RealtimeManager } from "@/lib/realtime/connection";
import { createEventDeduplicator } from "@/lib/realtime/deduplicate";
import { ReconnectStrategy } from "@/lib/realtime/reconnect";
import { RealtimeEventSchema } from "@/lib/realtime/event-schema";

describe("Realtime Synchronization & Resilience", () => {
  it("deduplicates events with identical eventId and evicts oldest on overflow", () => {
    const dedup = createEventDeduplicator(3);
    expect(dedup.isDuplicate("e-1")).toBe(false);
    expect(dedup.isDuplicate("e-1")).toBe(true);

    expect(dedup.isDuplicate("e-2")).toBe(false);
    expect(dedup.isDuplicate("e-3")).toBe(false);
    expect(dedup.size()).toBe(3);

    // Evicts e-1
    expect(dedup.isDuplicate("e-4")).toBe(false);
    expect(dedup.size()).toBe(3);
    expect(dedup.isDuplicate("e-1")).toBe(false); // e-1 was evicted
  });

  it("calculates exponential backoff delays with upper bounds", () => {
    const strategy = new ReconnectStrategy({
      initialDelayMs: 100,
      maxDelayMs: 1000,
      factor: 2,
      jitter: false,
    });

    expect(strategy.getNextDelay()).toBe(100);
    expect(strategy.getNextDelay()).toBe(200);
    expect(strategy.getNextDelay()).toBe(400);
    expect(strategy.getNextDelay()).toBe(800);
    expect(strategy.getNextDelay()).toBe(1000); // capped at maxDelayMs
    expect(strategy.getNextDelay()).toBe(1000);

    strategy.reset();
    expect(strategy.currentAttempts).toBe(0);
    expect(strategy.getNextDelay()).toBe(100);
  });

  it("validates RealtimeEventSchema and rejects invalid payloads", () => {
    const valid = {
      eventId: "evt-001",
      type: "document.processing.started",
      workspaceId: "ws-main",
      occurredAt: new Date().toISOString(),
      payload: { docId: "doc-123" },
    };
    expect(RealtimeEventSchema.safeParse(valid).success).toBe(true);

    const invalid = {
      eventId: "", // invalid min length
      type: "test",
    };
    expect(RealtimeEventSchema.safeParse(invalid).success).toBe(false);
  });

  it("isolates workspace events and dispatches strictly to matching listeners", () => {
    const manager = new RealtimeManager({ workspaceId: "ws-alpha" });
    const listener = vi.fn();
    manager.subscribe("document.processing.completed", listener);

    // Dispatches when workspace matches
    const validAlpha = {
      eventId: "evt-100",
      type: "document.processing.completed",
      workspaceId: "ws-alpha",
      occurredAt: new Date().toISOString(),
      payload: { docId: "doc-alpha" },
    };
    const handled1 = manager.handleIncomingRaw(validAlpha);
    expect(handled1).toBe(true);
    expect(listener).toHaveBeenCalledTimes(1);

    // Rejects cross-workspace event
    const crossWorkspace = {
      eventId: "evt-101",
      type: "document.processing.completed",
      workspaceId: "ws-beta",
      occurredAt: new Date().toISOString(),
      payload: { docId: "doc-beta" },
    };
    const handled2 = manager.handleIncomingRaw(crossWorkspace);
    expect(handled2).toBe(false);
    expect(listener).toHaveBeenCalledTimes(1); // not called again

    manager.disconnect();
  });
});
