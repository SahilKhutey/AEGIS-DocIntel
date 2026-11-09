# 05 — Notification Center

**Document Identifier**: `AEGIS-DOCINTEL-WP-UI-03-05`  
**Work Package**: `WP-UI-03: Application Shell`  
**Status**: APPROVED ARCHITECTURE  

---

## 1. Functional Scope

The Notification Center alerts analysts and reviewers to asynchronous pipeline events, processing completion, newly assigned human reviews, and system alerts.

---

## 2. Notification Data Contract

```ts
export type NotificationType =
  | "processing"
  | "intelligence"
  | "evidence"
  | "governance"
  | "system"
  | "security";

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  createdAt: string;
  readAt: string | null;
  resourceUrl?: string;
}

export interface NotificationListResponse {
  items: Notification[];
  unreadCount: number;
}
```

---

## 3. Interaction & Visual States

1. **Trigger Button**:
   - Bell icon with `aria-label="3 unread notifications"` (or `"Notifications"` when count is 0).
   - High-contrast badge displaying unread count (capped at `99+`).
   - `aria-haspopup="dialog"`, `aria-expanded={isOpen}`.
2. **Flyout Panel**:
   - Top header with "Mark all as read" button.
   - Scrollable list of notifications with semantic category badges.
   - Individual "Mark read" button per unread item.
   - Empty state illustration and text when no notifications exist.
3. **Keyboard Dismissal**:
   - Pressing <kbd>Escape</kbd> immediately closes the flyout and refocuses the trigger button.
   - Clicking outside the flyout dismisses it.

---

## 4. Backend Capability & Truth Assessment

- **Missing Dedicated Endpoint**: The FastAPI backend (`contracts/openapi.yaml`) does NOT expose a dedicated `/v1/notifications` endpoint.
- **Underlying Capabilities**: Event state is distributed across `/v1/jobs` (processing progress), `/v1/reviews` (governance queue items), and `/v1/intelligence/conflicts`.
- **Architectural Handling**: `DefaultNotificationService` documents the missing push/mark-read endpoint as **BLOCKED — backend capability missing**. The component accepts injectable props (`notifications`, `unreadNotificationCount`, `onMarkNotificationRead`) allowing screens and parent shells to map live job/review metrics into the center without synthetic mock operations.
