export type NotificationType =
  | "processing"
  | "intelligence"
  | "evidence"
  | "governance"
  | "system"
  | "security";

export type Notification = {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  createdAt: string;
  readAt: string | null;
  resourceUrl?: string;
};

export type NotificationListResponse = {
  items: Notification[];
  unreadCount: number;
  nextCursor?: string;
};
