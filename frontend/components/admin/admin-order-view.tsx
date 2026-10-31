"use client";

import Link from "next/link";
import { useState } from "react";
import useSWR from "swr";

import { StatusTimeline } from "@/components/orders/status-timeline";
import { api, type ApiError } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import { DELIVERY_METHOD_LABELS, ORDER_STATUS_LABELS, PAYMENT_METHOD_LABELS } from "@/lib/order-labels";
import { useAsyncAction } from "@/lib/use-async-action";
import type { Order, OrderStatus } from "@/types/orders";

/** What the admin's buttons say; the server decides which ones exist (`available_transitions`). */
function transitionLabel(status: OrderStatus, order: Order): string {
  switch (status) {
    case "preparing":
      return "Start preparing";
    case "ready_for_pickup":
      return order.delivery_method === "pickup" ? "Ready for the customer" : "Ready for a courier";
    case "delivered":
      return "Mark collected";
    default:
      return ORDER_STATUS_LABELS[status];
  }
}

export function AdminOrderView({ orderId }: { orderId: number }) {
  const key = `/orders/${orderId}`;
  const { data: order, error, mutate } = useSWR<Order, ApiError>(key, { refreshInterval: 15_000 });
  const action = useAsyncAction();
  const [confirmCancel, setConfirmCancel] = useState(false);

  async function run(request: () => Promise<Order>) {
    const updated = await action.run(request);
    if (updated) await mutate(updated, { revalidate: false });
    setConfirmCancel(false);
  }

  if (error) {
    return (
      <p role="alert" className="text-accent-strong">
        {error.message}
      </p>
    );
  }
  if (!order) return <div className="h-96 animate-pulse rounded-xl bg-surface" aria-busy />;

  return (
    <div className="max-w-4xl">
      <Link href="/admin/orders" className="text-sm text-muted-ink hover:text-ink">
        ← Orders
      </Link>
      <div className="mt-2 flex flex-wrap items-baseline gap-x-4 gap-y-1">
        <h1 className="font-serif text-3xl text-ink">Order #{order.id}</h1>
        <span className="text-muted-ink">
          {order.restaurant.name} · {ORDER_STATUS_LABELS[order.status]}
        </span>
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-2">
        {order.available_transitions.map((status) => (
          <button
            key={status}
            type="button"
            disabled={action.pending}
            onClick={() => void run(() => api.patch<Order>(`/orders/${order.id}/status`, { status }))}
            className="rounded-full bg-accent px-4 py-2 text-sm font-semibold text-white hover:bg-accent-strong disabled:opacity-50"
          >
            {transitionLabel(status, order)}
          </button>
        ))}
        {order.can_cancel &&
          (confirmCancel ? (
            <span className="inline-flex items-center gap-2 rounded-full bg-surface py-1 pl-4 pr-1 text-sm">
              Cancel and refund?
              <button
                type="button"
                disabled={action.pending}
                onClick={() => void run(() => api.post<Order>(`/orders/${order.id}/cancel`))}
                className="rounded-full bg-accent-strong px-3 py-1.5 font-semibold text-white disabled:opacity-50"
              >
                Yes, cancel
              </button>
              <button type="button" onClick={() => setConfirmCancel(false)} className="rounded-full px-3 py-1.5 hover:bg-background">
                Keep
              </button>
            </span>
          ) : (
            <button type="button" onClick={() => setConfirmCancel(true)} className="rounded-full border border-line px-4 py-2 text-sm font-medium text-ink hover:border-accent-strong hover:text-accent-strong">
              Cancel order
            </button>
          ))}
        {order.available_transitions.length === 0 && !order.can_cancel && (
          <p className="text-sm text-muted-ink">
            {order.status === "ready_for_pickup" || order.status === "delivering"
              ? "Waiting for the courier."
              : order.status === "pending_payment"
                ? "Waiting for the customer's payment."
                : "No actions left for this order."}
          </p>
        )}
      </div>
      {action.error && (
        <p role="alert" className="mt-2 text-sm text-accent-strong">
          {action.error}
        </p>
      )}

      <div className="mt-8 grid gap-8 md:grid-cols-[1fr_18rem]">
        <section aria-labelledby="admin-items">
          <h2 id="admin-items" className="font-sans text-xs font-semibold uppercase tracking-[0.18em] text-sage">
            Items
          </h2>
          <ul className="mt-2 divide-y divide-line rounded-xl border border-line bg-card text-sm">
            {order.items.map((item) => (
              <li key={`${item.dish_id}-${item.name}`} className="flex justify-between gap-3 px-4 py-2.5">
                <span>
                  <span className="tabular-nums text-muted-ink">{item.quantity} × </span>
                  {item.name}
                </span>
                <span className="tabular-nums">{formatPrice(item.price * item.quantity)}</span>
              </li>
            ))}
          </ul>
          <dl className="mt-3 ml-auto max-w-xs space-y-1 text-sm">
            <div className="flex justify-between">
              <dt className="text-muted-ink">Dishes</dt>
              <dd className="tabular-nums">{formatPrice(order.subtotal)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-ink">Delivery</dt>
              <dd className="tabular-nums">{formatPrice(order.delivery_fee)}</dd>
            </div>
            {order.discount > 0 && (
              <div className="flex justify-between">
                <dt className="text-muted-ink">Discounts{order.bonus_points_used > 0 ? ` (${order.bonus_points_used} pts)` : ""}</dt>
                <dd className="tabular-nums text-sage">−{formatPrice(order.discount)}</dd>
              </div>
            )}
            <div className="flex justify-between border-t border-line pt-1.5 font-medium">
              <dt>Total</dt>
              <dd className="tabular-nums">{formatPrice(order.total)}</dd>
            </div>
          </dl>

          <h2 className="mt-8 font-sans text-xs font-semibold uppercase tracking-[0.18em] text-sage">Progress</h2>
          <div className="mt-3">
            <StatusTimeline order={order} />
          </div>
        </section>

        <aside className="h-fit space-y-4 rounded-xl bg-surface p-5 text-sm">
          <div>
            <p className="text-xs uppercase tracking-wider text-muted-ink">Customer</p>
            <p className="mt-0.5 font-medium text-ink">{order.customer?.name}</p>
            {order.customer?.phone && <p className="text-muted-ink">{order.customer.phone}</p>}
          </div>
          <div>
            <p className="text-xs uppercase tracking-wider text-muted-ink">{DELIVERY_METHOD_LABELS[order.delivery_method].title}</p>
            <p className="mt-0.5 text-ink">{order.delivery_method === "pickup" ? "Collected at the restaurant" : order.delivery_address}</p>
            {order.delivery_note && <p className="text-muted-ink">{order.delivery_note}</p>}
          </div>
          <div>
            <p className="text-xs uppercase tracking-wider text-muted-ink">Payment</p>
            <p className="mt-0.5 text-ink">
              {PAYMENT_METHOD_LABELS[order.payment_method]} · {order.payment_status}
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}
