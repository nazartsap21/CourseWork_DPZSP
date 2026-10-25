"use client";

import { MapPin } from "lucide-react";
import dynamic from "next/dynamic";
import Link from "next/link";
import useSWR from "swr";

import type { ApiError } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import { DELIVERY_METHOD_LABELS, PAYMENT_METHOD_LABELS } from "@/lib/order-labels";
import { usePayAgain } from "@/lib/payments";
import type { Order, Tracking } from "@/types/orders";

import { OrderActions } from "./order-actions";
import { StatusTimeline } from "./status-timeline";

const RouteMap = dynamic(() => import("@/components/maps/route-map"), {
  ssr: false,
  loading: () => <div className="h-full w-full animate-pulse bg-surface" />,
});

const POLL_MS = 5_000;
const timeFormat = new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit" });

function isFinished(order: Order | undefined): boolean {
  return order?.status === "delivered" || order?.status === "cancelled";
}

// SWR calls this with the latest data: poll while the order is moving, stop once it's done.
const pollWhileActive = (order: Order | undefined) => (isFinished(order) ? 0 : POLL_MS);

function expectedBy(order: Order): string | null {
  if (!order.estimated_delivery_minutes) return null;
  const at = new Date(new Date(order.created_at).getTime() + order.estimated_delivery_minutes * 60_000);
  return timeFormat.format(at);
}

/** Big status line at the top: what is happening now and what to expect. */
function headline(order: Order, tracking: Tracking | undefined): { title: string; detail: string | null } {
  const isPickup = order.delivery_method === "pickup";
  const by = expectedBy(order);
  const minutes = tracking?.courier?.minutes_left;
  switch (order.status) {
    case "pending_payment":
      return { title: "Waiting for payment", detail: "The kitchen starts as soon as the payment is confirmed." };
    case "accepted":
      return { title: "Order accepted", detail: by ? `${isPickup ? "Ready" : "Expected"} by ${by}` : null };
    case "preparing":
      return { title: `${order.restaurant.name} is cooking`, detail: by ? `${isPickup ? "Ready" : "Expected"} by ${by}` : null };
    case "ready_for_pickup":
      return isPickup
        ? { title: "Ready for pickup", detail: `Collect it at ${order.restaurant.address}` }
        : { title: "Ready, a courier is coming for it", detail: by ? `Expected by ${by}` : null };
    case "delivering":
      return {
        title: "On the way",
        detail:
          minutes === undefined ? null : minutes <= 1 ? "The courier is almost at your door" : `Arrives in about ${minutes} min`,
      };
    case "delivered":
      return { title: isPickup ? "Collected" : "Delivered", detail: "Enjoy your meal!" };
    case "cancelled":
      return { title: "Order cancelled", detail: null };
  }
}

/** Order tracking: live status, courier on the map and the timeline. Polls every 5 s until the order is done. */
export function OrderView({ orderId }: { orderId: number }) {
  const valid = Number.isInteger(orderId) && orderId > 0;
  const { data: order, error } = useSWR<Order, ApiError>(valid ? `/orders/${orderId}` : null, {
    refreshInterval: pollWhileActive,
  });
  // The tracking poll follows the order: it stops when the order is finished.
  const { data: tracking } = useSWR<Tracking, ApiError>(valid && order ? `/orders/${orderId}/tracking` : null, {
    refreshInterval: isFinished(order) ? 0 : POLL_MS,
  });
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
  if (error && !order) {
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
      <main className="mx-auto w-full max-w-6xl flex-1 space-y-4 px-4 pt-10 sm:px-6 lg:px-8" aria-busy>
        <div className="h-10 w-64 animate-pulse rounded-lg bg-surface" />
        <div className="grid gap-8 lg:grid-cols-[1fr_22rem]">
          <div className="h-80 animate-pulse rounded-xl bg-surface" />
          <div className="h-80 animate-pulse rounded-xl bg-surface" />
        </div>
      </main>
    );
  }

  const isPickup = order.delivery_method === "pickup";
  const { title, detail } = headline(order, tracking);
  const showMap = order.status !== "cancelled";

  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-4 pb-16 pt-8 sm:px-6 lg:px-8">
      <p className="text-sm text-muted-ink">
        Order #{order.id} · {order.restaurant.name}
      </p>
      <h1 className="mt-1 font-serif text-4xl tracking-tight text-ink sm:text-5xl" aria-live="polite">
        {title}
      </h1>
      {detail && <p className="mt-2 text-lg text-muted-ink">{detail}</p>}

      {order.status === "pending_payment" && (
        <div className="mt-5 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={() => void payment.payAgain()}
            disabled={payment.pending}
            className="rounded-full bg-accent px-5 py-2.5 text-sm font-semibold text-white hover:bg-accent-strong disabled:opacity-50"
          >
            {payment.pending ? "Opening payment…" : `Pay ${formatPrice(order.total)}`}
          </button>
          {payment.error && (
            <p role="alert" className="text-sm text-accent-strong">
              {payment.error}
            </p>
          )}
        </div>
      )}

      <OrderActions order={order} />

      <div className="mt-8 grid gap-8 lg:grid-cols-[1fr_22rem]">
        <div className="space-y-8">
          {showMap && (
            <div className="h-72 overflow-hidden rounded-xl border border-line sm:h-96">
              {tracking ? (
                <RouteMap
                  restaurant={tracking.restaurant}
                  destination={tracking.destination}
                  route={tracking.route}
                  courier={tracking.courier}
                />
              ) : (
                <div className="h-full w-full animate-pulse bg-surface" />
              )}
            </div>
          )}

          <section aria-labelledby="timeline-title">
            <h2 id="timeline-title" className="font-sans text-xs font-semibold uppercase tracking-[0.18em] text-sage">
              Progress
            </h2>
            <div className="mt-4">
              <StatusTimeline order={order} />
            </div>
          </section>
        </div>

        <aside className="h-fit space-y-6 rounded-xl bg-surface p-5 lg:sticky lg:top-6">
          <div className="flex items-start gap-2 text-sm text-ink">
            <MapPin aria-hidden className="mt-0.5 h-4 w-4 shrink-0 text-sage" />
            {isPickup ? (
              <span>
                Pick up at {order.restaurant.name}
                <span className="block text-muted-ink">{order.restaurant.address}</span>
              </span>
            ) : (
              <span>
                {order.delivery_address}
                {order.delivery_note && <span className="block text-muted-ink">{order.delivery_note}</span>}
              </span>
            )}
          </div>

          <dl className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-xs uppercase tracking-[0.14em] text-muted-ink">Delivery</dt>
              <dd className="mt-0.5 text-ink">{DELIVERY_METHOD_LABELS[order.delivery_method].title}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-[0.14em] text-muted-ink">Payment</dt>
              <dd className="mt-0.5 text-ink">
                {PAYMENT_METHOD_LABELS[order.payment_method]}
                {order.payment_status === "paid" && <span className="text-sage"> · paid</span>}
              </dd>
            </div>
          </dl>

          <ul className="space-y-1.5 border-t border-line pt-4 text-sm">
            {order.items.map((item) => (
              <li key={`${item.dish_id}-${item.name}`} className="flex justify-between gap-3">
                <span className="text-ink">
                  <span className="tabular-nums text-muted-ink">{item.quantity} × </span>
                  {item.name}
                </span>
                <span className="tabular-nums text-ink">{formatPrice(item.price * item.quantity)}</span>
              </li>
            ))}
          </ul>

          <dl className="space-y-1.5 border-t border-line pt-4 text-sm">
            <div className="flex justify-between">
              <dt className="text-muted-ink">Dishes</dt>
              <dd className="tabular-nums text-ink">{formatPrice(order.subtotal)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-ink">Delivery</dt>
              <dd className="tabular-nums text-ink">
                {order.delivery_fee === 0 ? "Free" : formatPrice(order.delivery_fee)}
              </dd>
            </div>
            {order.discount > 0 && (
              <div className="flex justify-between">
                <dt className="text-muted-ink">
                  Discounts{order.bonus_points_used > 0 ? ` (incl. ${order.bonus_points_used} points)` : ""}
                </dt>
                <dd className="tabular-nums text-sage">−{formatPrice(order.discount)}</dd>
              </div>
            )}
            <div className="flex items-baseline justify-between border-t border-line pt-2">
              <dt className="font-medium text-ink">Total</dt>
              <dd className="font-serif text-xl tabular-nums text-ink">{formatPrice(order.total)}</dd>
            </div>
          </dl>
        </aside>
      </div>
    </main>
  );
}
