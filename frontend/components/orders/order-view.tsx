"use client";

import { CheckCircle2, Clock, MapPin } from "lucide-react";
import Link from "next/link";
import useSWR from "swr";

import type { ApiError } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import { usePayAgain } from "@/lib/payments";
import { DELIVERY_METHOD_LABELS, ORDER_STATUS_LABELS, PAYMENT_METHOD_LABELS } from "@/lib/order-labels";
import type { Order } from "@/types/orders";

const timeFormat = new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit" });

function expectedBy(order: Order): string | null {
  if (!order.estimated_delivery_minutes) return null;
  const at = new Date(new Date(order.created_at).getTime() + order.estimated_delivery_minutes * 60_000);
  return timeFormat.format(at);
}

/** Order confirmation and details. Live tracking (map, polling) is added on top of this later. */
export function OrderView({ orderId }: { orderId: number }) {
  const valid = Number.isInteger(orderId) && orderId > 0;
  const { data: order, error } = useSWR<Order, ApiError>(valid ? `/orders/${orderId}` : null);
  const payment = usePayAgain(orderId);

  if (!valid || error?.status === 404) {
    return (
      <main className="mx-auto w-full max-w-xl flex-1 px-4 py-20 text-center">
        <h1 className="font-serif text-4xl text-ink">Order not found</h1>
        <Link href="/" className="mt-6 inline-block text-sm font-semibold text-accent-strong hover:underline">
          Back to restaurants
        </Link>
      </main>
    );
  }
  if (error) {
    return (
      <main className="mx-auto w-full max-w-xl flex-1 px-4 py-20 text-center">
        <p role="alert" className="text-accent-strong">
          {error.message}
        </p>
      </main>
    );
  }
  if (!order) {
    return (
      <main className="mx-auto w-full max-w-3xl flex-1 space-y-4 px-4 pt-10" aria-busy>
        <div className="h-10 w-64 animate-pulse rounded-lg bg-surface" />
        <div className="h-48 animate-pulse rounded-xl bg-surface" />
      </main>
    );
  }

  const by = expectedBy(order);
  const isPickup = order.delivery_method === "pickup";

  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-4 pb-16 pt-8 sm:px-6">
      {order.status !== "pending_payment" && (
        <p className="inline-flex items-center gap-2 text-sm font-medium text-sage">
          <CheckCircle2 aria-hidden className="h-4 w-4" />
          Order placed
        </p>
      )}
      <h1 className="mt-2 font-serif text-4xl tracking-tight text-ink">Order #{order.id}</h1>
      <p className="mt-1 text-muted-ink">from {order.restaurant.name}</p>

      <div className="mt-6 flex flex-wrap gap-x-8 gap-y-3 border-y border-line py-4">
        <div>
          <p className="text-xs uppercase tracking-[0.14em] text-muted-ink">Status</p>
          <p className="mt-1 font-medium text-ink">{ORDER_STATUS_LABELS[order.status]}</p>
        </div>
        {by && order.status !== "cancelled" && order.status !== "delivered" && (
          <div>
            <p className="text-xs uppercase tracking-[0.14em] text-muted-ink">{isPickup ? "Ready by" : "Expected by"}</p>
            <p className="mt-1 inline-flex items-center gap-1.5 font-medium text-ink">
              <Clock aria-hidden className="h-4 w-4 text-sage" />
              {by}
            </p>
          </div>
        )}
        <div>
          <p className="text-xs uppercase tracking-[0.14em] text-muted-ink">Delivery</p>
          <p className="mt-1 font-medium text-ink">{DELIVERY_METHOD_LABELS[order.delivery_method].title}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.14em] text-muted-ink">Payment</p>
          <p className="mt-1 font-medium text-ink">
            {PAYMENT_METHOD_LABELS[order.payment_method]}
            {order.payment_status === "paid" && <span className="ml-1 text-sm text-sage">· paid</span>}
          </p>
        </div>
      </div>

      {order.status === "pending_payment" && (
        <div className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-lg bg-surface px-4 py-3">
          <p className="text-sm text-ink">The kitchen starts cooking as soon as the payment is confirmed.</p>
          <button
            type="button"
            onClick={() => void payment.payAgain()}
            disabled={payment.pending}
            className="rounded-full bg-accent px-4 py-2 text-sm font-semibold text-white hover:bg-accent-strong disabled:opacity-50"
          >
            {payment.pending ? "Opening payment…" : `Pay ${formatPrice(order.total)}`}
          </button>
          {payment.error && (
            <p role="alert" className="w-full text-sm text-accent-strong">
              {payment.error}
            </p>
          )}
        </div>
      )}

      <p className="mt-6 inline-flex items-start gap-2 text-ink">
        <MapPin aria-hidden className="mt-0.5 h-4 w-4 shrink-0 text-sage" />
        <span>
          {isPickup ? (
            <>
              Pick up at {order.restaurant.name}
              <span className="block text-sm text-muted-ink">{order.restaurant.address}</span>
            </>
          ) : (
            <>
              {order.delivery_address}
              {order.delivery_note && <span className="block text-sm text-muted-ink">{order.delivery_note}</span>}
            </>
          )}
        </span>
      </p>

      <ul className="mt-8 border-t border-line">
        {order.items.map((item) => (
          <li key={`${item.dish_id}-${item.name}`} className="flex justify-between gap-4 border-b border-line py-3 text-sm">
            <span className="text-ink">
              <span className="tabular-nums text-muted-ink">{item.quantity} × </span>
              {item.name}
            </span>
            <span className="tabular-nums text-ink">{formatPrice(item.price * item.quantity)}</span>
          </li>
        ))}
      </ul>

      <dl className="mt-4 ml-auto max-w-xs space-y-1.5 text-sm">
        <div className="flex justify-between">
          <dt className="text-muted-ink">Dishes</dt>
          <dd className="tabular-nums text-ink">{formatPrice(order.subtotal)}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-muted-ink">Delivery</dt>
          <dd className="tabular-nums text-ink">{order.delivery_fee === 0 ? "Free" : formatPrice(order.delivery_fee)}</dd>
        </div>
        {order.discount > 0 && (
          <div className="flex justify-between">
            <dt className="text-muted-ink">
              Discounts{order.bonus_points_used > 0 ? ` (incl. ${order.bonus_points_used} points)` : ""}
            </dt>
            <dd className="tabular-nums text-sage">−{formatPrice(order.discount)}</dd>
          </div>
        )}
        <div className="flex justify-between border-t border-line pt-2">
          <dt className="font-medium text-ink">Total</dt>
          <dd className="font-serif text-xl tabular-nums text-ink">{formatPrice(order.total)}</dd>
        </div>
      </dl>
    </main>
  );
}
