export type NotificationType = "order_status" | "bonus_points" | "promo";

export interface AppNotification {
  id: number;
  type: NotificationType;
  message: string;
  order_id: number | null;
  is_read: boolean;
  created_at: string;
}

export interface Inbox {
  items: AppNotification[];
  unread_count: number;
}
