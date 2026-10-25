"use client";

import { RotateCcw } from "lucide-react";
import { useState } from "react";
import { useSWRConfig } from "swr";

import { ApiError, api } from "@/lib/api";
import { useReorder } from "@/lib/reorder";
import type { Order } from "@/types/orders";

/** "Cancel order" (with an inline confirmation) and "Order again" for the tracking page. */
export function OrderActions({ order }: { order: Order }) {
  const { mutate } = useSWRConfig();
  const { reorder, pendingId, errorFor } = useReorder();
  const [confirming, setConfirming] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [cancelError, setCancelError] = useState<string | null>(null);
  const finished = order.status === "delivered" || order.status === "cancelled";

  async function cancel() {
    setCancelling(true);
    setCancelError(null);
    try {
      const updated = await api.post<Order>(`/orders/${order.id}/cancel`);
      await mutate(`/orders/${order.id}`, updated, { revalidate: false });
      setConfirming(false);
    } catch (error) {
      if (!(error instanceof ApiError)) throw error;
      setCancelError(error.message);
    } finally {
      setCancelling(false);
    }
  }

  if (!order.can_cancel && !finished) return null;

  return (
    <div className="mt-5 space-y-2">
      <div className="flex flex-wrap items-center gap-3">
        {finished && (
          <button
            type="button"
            onClick={() => void reorder(order.id)}
            disabled={pendingId !== null}
            className="inline-flex items-center gap-2 rounded-full bg-accent px-5 py-2.5 text-sm font-semibold text-white hover:bg-accent-strong disabled:opacity-50"
          >
            <RotateCcw aria-hidden className="h-4 w-4" />
            {pendingId === order.id ? "Adding to cart…" : "Order again"}
          </button>
        )}
        {order.can_cancel &&
          (confirming ? (
            <span className="inline-flex flex-wrap items-center gap-2 rounded-full bg-surface py-1 pl-4 pr-1 text-sm text-ink">
              Cancel this order?
              <button
                type="button"
                onClick={() => void cancel()}
                disabled={cancelling}
                className="rounded-full bg-accent-strong px-3 py-1.5 font-semibold text-white disabled:opacity-50"
              >
                {cancelling ? "Cancelling…" : "Yes, cancel"}
              </button>
              <button
                type="button"
                onClick={() => setConfirming(false)}
                disabled={cancelling}
                className="rounded-full px-3 py-1.5 font-medium text-ink hover:bg-background"
              >
                Keep it
              </button>
            </span>
          ) : (
            <button
              type="button"
              onClick={() => setConfirming(true)}
              className="rounded-full border border-line px-4 py-2 text-sm font-medium text-ink hover:border-accent-strong hover:text-accent-strong"
            >
              Cancel order
            </button>
          ))}
      </div>
      {order.can_cancel && confirming && (
        <p className="text-xs text-muted-ink">
          {order.payment_status === "paid" ? "The payment is refunded to your card. " : ""}
          {order.bonus_points_used > 0 ? `${order.bonus_points_used} points go back to your balance.` : ""}
        </p>
      )}
      {(cancelError || errorFor(order.id)) && (
        <p role="alert" className="text-sm text-accent-strong">
          {cancelError ?? errorFor(order.id)}
        </p>
      )}
    </div>
  );
}
