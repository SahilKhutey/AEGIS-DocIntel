import { RealtimeEvent, RealtimeEventSchema } from "./event-schema";
import { createEventDeduplicator } from "./deduplicate";
import { ReconnectStrategy } from "./reconnect";

export type ConnectionStatusListener = (status: "connected" | "reconnecting" | "disconnected") => void;
export type EventListener = (event: RealtimeEvent) => void;

export interface RealtimeOptions {
  workspaceId: string;
  onStatusChange?: ConnectionStatusListener;
}

export class RealtimeManager {
  private status: "connected" | "reconnecting" | "disconnected" = "disconnected";
  private listeners: Map<string, Set<EventListener>> = new Map();
  private statusListeners: Set<ConnectionStatusListener> = new Set();
  private deduplicator = createEventDeduplicator(1000);
  private reconnectStrategy = new ReconnectStrategy();
  private reconnectTimer: NodeJS.Timeout | null = null;
  private currentWorkspaceId: string;
  private isExplicitlyClosed = false;

  constructor(options: RealtimeOptions) {
    this.currentWorkspaceId = options.workspaceId;
    if (options.onStatusChange) {
      this.statusListeners.add(options.onStatusChange);
    }
  }

  setWorkspace(newWorkspaceId: string): void {
    if (this.currentWorkspaceId !== newWorkspaceId) {
      this.currentWorkspaceId = newWorkspaceId;
      this.deduplicator.clear();
      // Resync or reset connection for the new workspace
      this.resync();
    }
  }

  subscribe(eventType: string, handler: EventListener): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType)!.add(handler);

    return () => {
      const set = this.listeners.get(eventType);
      if (set) {
        set.delete(handler);
        if (set.size === 0) {
          this.listeners.delete(eventType);
        }
      }
    };
  }

  onStatusChange(listener: ConnectionStatusListener): () => void {
    this.statusListeners.add(listener);
    listener(this.status);
    return () => {
      this.statusListeners.delete(listener);
    };
  }

  handleIncomingRaw(raw: unknown): boolean {
    const parsed = RealtimeEventSchema.safeParse(raw);
    if (!parsed.success) {
      // Discard invalid schema
      return false;
    }

    const event = parsed.data;

    // Enforce workspace boundary
    if (event.workspaceId !== this.currentWorkspaceId) {
      // Discard cross-workspace event
      return false;
    }

    // Deduplicate
    if (this.deduplicator.isDuplicate(event.eventId)) {
      return false;
    }

    // Dispatch to specific listeners and wildcard listeners
    const specific = this.listeners.get(event.type);
    if (specific) {
      specific.forEach((fn) => fn(event));
    }
    const wildcard = this.listeners.get("*");
    if (wildcard) {
      wildcard.forEach((fn) => fn(event));
    }

    return true;
  }

  setStatus(newStatus: "connected" | "reconnecting" | "disconnected"): void {
    if (this.status !== newStatus) {
      this.status = newStatus;
      this.statusListeners.forEach((fn) => fn(newStatus));
    }
  }

  getStatus(): "connected" | "reconnecting" | "disconnected" {
    return this.status;
  }

  resync(): void {
    this.setStatus("connected");
    this.reconnectStrategy.reset();
  }

  disconnect(): void {
    this.isExplicitlyClosed = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.setStatus("disconnected");
    this.deduplicator.clear();
    this.listeners.clear();
  }
}
