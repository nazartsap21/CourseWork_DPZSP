"use client";

import { Bell } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useRef, useState } from "react";
import useSWR from "swr";

import { api } from "@/lib/api";
import { formatRelativeTime } from "@/lib/format";
import { useDismiss } from "@/lib/use-dismiss";
import type { AppNotification, Inbox } from "@/types/notifications";

const INBOX_KEY = "/notifications";
const POLL_MS = 15_000;

/** In-app notifications: unread badge in the header, polled every 15 s. */
export function NotificationBell({ canOpenOrders }: { canOpenOrders: boolean }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const close = useCallback(() => setOpen(false), []);
  const containerRef = useRef<HTMLDivElement>(null);
  useDismiss(containerRef, open, close);

  const { data: inbox, mutate } = useSWR<Inbox>(INBOX_KEY, { refreshInterval: POLL_MS });
  const unread = inbox?.unread_count ?? 0;

  // Optimistic: the badge and the dot update at once; the server confirms in the background.
  const markRead = (notification: AppNotification) => {
    if (notification.is_read || !inbox) return;
    void mutate(
      api.patch(`/notifications/${notification.id}/read`).then(() => undefined),
      {
        optimisticData: {
          unread_count: Math.max(inbox.unread_count - 1, 0),
          items: inbox.items.map((n) => (n.id === notification.id ? { ...n, is_read: true } : n)),
        },
        populateCache: false,
        revalidate: true,
      },
    );
  };

  const markAllRead = () => {
    if (!inbox) return;
    void mutate(
      api.post("/notifications/read-all").then(() => undefined),
      {
        optimisticData: { unread_count: 0, items: inbox.items.map((n) => ({ ...n, is_read: true })) },
        populateCache: false,
        revalidate: true,
      },
    );
  };

  const openNotification = (notification: AppNotification) => {
    markRead(notification);
    if (notification.order_id && canOpenOrders) {
      setOpen(false);
      router.push(`/orders/${notification.order_id}`);
    }
  };

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-haspopup="dialog"
        aria-label={unread > 0 ? `Notifications, ${unread} unread` : "Notifications"}
        className="relative flex h-9 w-9 items-center justify-center rounded-full text-ink transition hover:bg-surface"
      >
        <Bell aria-hidden className="h-5 w-5" />
        {unread > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-accent px-1 text-[0.65rem] font-semibold leading-none text-white">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      {open && (
        <div
          role="dialog"
          aria-label="Notifications"
          // Phones: pinned to the screen edges (the bell isn't the rightmost header item).
          className="fixed inset-x-4 top-16 z-20 overflow-hidden rounded-xl border border-line bg-card shadow-[0_12px_32px_rgba(34,25,22,0.12)] sm:absolute sm:inset-x-auto sm:right-0 sm:top-auto sm:mt-2 sm:w-[22rem]"
        >
          <div className="flex items-center justify-between border-b border-line px-4 py-3">
            <p className="font-serif text-lg text-ink">Notifications</p>
            {unread > 0 && (
              <button type="button" onClick={markAllRead} className="text-xs font-medium text-accent-strong hover:underline">
                Mark all as read
              </button>
            )}
          </div>
          {!inbox ? (
            <div className="space-y-2 p-4" aria-busy>
              {Array.from({ length: 3 }, (_, i) => (
                <div key={i} className="h-10 animate-pulse rounded bg-surface" />
              ))}
            </div>
          ) : inbox.items.length === 0 ? (
            <p className="px-4 py-8 text-center text-sm text-muted-ink">
              Nothing yet. Order updates will show up here.
            </p>
          ) : (
            <ul className="max-h-96 overflow-y-auto">
              {inbox.items.map((notification) => (
                <li key={notification.id} className="border-b border-line last:border-b-0">
                  <button
                    type="button"
                    onClick={() => openNotification(notification)}
                    className="flex w-full gap-3 px-4 py-3 text-left transition hover:bg-surface"
                  >
                    <span
                      aria-hidden
                      className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${notification.is_read ? "bg-transparent" : "bg-accent"}`}
                    />
                    <span className="min-w-0">
                      <span className={`block text-sm ${notification.is_read ? "text-muted-ink" : "text-ink"}`}>
                        {notification.message}
                      </span>
                      <span className="mt-0.5 block text-xs text-muted-ink">
                        {formatRelativeTime(notification.created_at)}
                        {!notification.is_read && <span className="sr-only"> · unread</span>}
                      </span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
