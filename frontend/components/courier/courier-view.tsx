"use client";

import { Banknote, MapPin, Phone, Store } from "lucide-react";
import dynamic from "next/dynamic";
import { useState } from "react";
import useSWR, { useSWRConfig } from "swr";

import { ApiError, api } from "@/lib/api";
import { formatPrice, formatRelativeTime, pluralize } from "@/lib/format";
import type { CourierOrder, OrderStatus, Tracking } from "@/types/orders";

const RouteMap = dynamic(() => import("@/components/maps/route-map"), {
  ssr: false,
  loading: () => <div className="h-full w-full animate-pulse bg-surface" />,
});

const ACTIVE_KEY = "/courier/orders/active";
const AVAILABLE_KEY = "/courier/orders/available";
const POLL_MS = 10_000;

const ACTION_LABELS: Partial<Record<OrderStatus, string>> = {
  delivering: "Picked up",
  delivered: "Delivered",
};

function itemsSummary(order: CourierOrder): string {
  const count = order.items.reduce((sum, item) => sum + item.quantity, 0);
  return pluralize(count, "item", "items");
}

function useOrderAction() {
  const { mutate } = useSWRConfig();
  const [pendingId, setPendingId] = useState<number | null>(null);
  const [errors, setErrors] = useState<Record<number, string>>({});

  async function run(orderId: number, request: () => Promise<unknown>) {
    setPendingId(orderId);
    setErrors((current) => ({ ...current, [orderId]: "" }));
    try {
      await request();
    } catch (error) {
      if (!(error instanceof ApiError)) throw error;
      setErrors((current) => ({ ...current, [orderId]: error.message }));
    } finally {
      setPendingId(null);
      // Both lists change: a taken order moves from "available" to "active".
      await Promise.all([mutate(ACTIVE_KEY), mutate(AVAILABLE_KEY)]);
    }
  }

  return {
    pendingId,
    errorFor: (orderId: number) => errors[orderId] || null,
    take: (id: number) => run(id, () => api.post(`/courier/orders/${id}/take`)),
    setStatus: (id: number, status: OrderStatus) => run(id, () => api.patch(`/orders/${id}/status`, { status })),
  };
}

function DeliveryMap({ orderId }: { orderId: number }) {
  const { data } = useSWR<Tracking>(`/orders/${orderId}/tracking`, { refreshInterval: POLL_MS });
  return (
    <div className="h-48 overflow-hidden rounded-lg border border-line sm:h-56">
      {data ? (
        <RouteMap restaurant={data.restaurant} destination={data.destination} route={data.route} courier={data.courier} />
      ) : (
        <div className="h-full w-full animate-pulse bg-surface" />
      )}
    </div>
  );
}

function ActiveDelivery({ order, actions }: { order: CourierOrder; actions: ReturnType<typeof useOrderAction> }) {
  const collectCash = order.payment_method === "cash" && order.payment_status !== "paid";
  const pending = actions.pendingId === order.id;

  return (
    <article className="rounded-xl border border-line bg-card p-4 sm:p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="font-serif text-xl text-ink">Order #{order.id}</h3>
        <span className="text-sm font-medium text-sage">
          {order.status === "delivering" ? "On the way" : "Go to the restaurant"}
        </span>
      </div>

      <ol className="mt-4 space-y-3 text-sm">
        <li className="flex gap-3">
          <Store aria-hidden className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
          <span>
            <span className="font-medium text-ink">{order.restaurant.name}</span>
            <span className="block text-muted-ink">{order.restaurant.address}</span>
            <span className="block text-muted-ink">{itemsSummary(order)}</span>
          </span>
        </li>
        <li className="flex gap-3">
          <MapPin aria-hidden className="mt-0.5 h-4 w-4 shrink-0 text-ink" />
          <span>
            <span className="font-medium text-ink">{order.delivery_address}</span>
            {order.delivery_note && <span className="block text-muted-ink">{order.delivery_note}</span>}
            {order.customer && (
              <span className="mt-1 flex flex-wrap items-center gap-x-2 text-muted-ink">
                {order.customer.name}
                {order.customer.phone && (
                  <a href={`tel:${order.customer.phone}`} className="inline-flex items-center gap-1 text-ink underline-offset-2 hover:underline">
                    <Phone aria-hidden className="h-3.5 w-3.5" />
                    {order.customer.phone}
                  </a>
                )}
              </span>
            )}
          </span>
        </li>
      </ol>

      {collectCash && (
        <p className="mt-4 inline-flex items-center gap-2 rounded-full bg-saffron/20 px-3 py-1 text-sm font-medium text-ink">
          <Banknote aria-hidden className="h-4 w-4" />
          Collect {formatPrice(order.total)} in cash
        </p>
      )}

      {order.status === "delivering" && (
        <div className="mt-4">
          <DeliveryMap orderId={order.id} />
        </div>
      )}

      {actions.errorFor(order.id) && (
        <p role="alert" className="mt-3 text-sm text-accent-strong">
          {actions.errorFor(order.id)}
        </p>
      )}
      <div className="mt-4 flex flex-wrap gap-2">
        {order.available_transitions.map((status) => (
          <button
            key={status}
            type="button"
            disabled={pending}
            onClick={() => void actions.setStatus(order.id, status)}
            className="rounded-full bg-accent px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-accent-strong disabled:opacity-50"
          >
            {pending ? "Saving…" : (ACTION_LABELS[status] ?? status)}
          </button>
        ))}
      </div>
    </article>
  );
}

function AvailableOrder({ order, actions }: { order: CourierOrder; actions: ReturnType<typeof useOrderAction> }) {
  const pending = actions.pendingId === order.id;
  return (
    <li className="flex flex-wrap items-center justify-between gap-3 border-b border-line py-4">
      <div className="min-w-0 text-sm">
        <p className="font-medium text-ink">
          {order.restaurant.name} <span className="font-normal text-muted-ink">→ {order.delivery_address}</span>
        </p>
        <p className="mt-0.5 text-muted-ink">
          #{order.id} · {itemsSummary(order)} · placed {formatRelativeTime(order.created_at)}
          {order.payment_method === "cash" && ` · cash ${formatPrice(order.total)}`}
        </p>
        {actions.errorFor(order.id) && (
          <p role="alert" className="mt-1 text-accent-strong">
            {actions.errorFor(order.id)}
          </p>
        )}
      </div>
      <button
        type="button"
        disabled={pending}
        onClick={() => void actions.take(order.id)}
        className="rounded-full border border-ink px-4 py-2 text-sm font-semibold text-ink transition hover:bg-ink hover:text-background disabled:opacity-50"
      >
        {pending ? "Taking…" : "Take order"}
      </button>
    </li>
  );
}

/** Courier workspace: own deliveries first, then orders waiting for any courier. Polls every 10 s. */
export function CourierView() {
  const active = useSWR<{ items: CourierOrder[] }, ApiError>(ACTIVE_KEY, { refreshInterval: POLL_MS });
  const available = useSWR<{ items: CourierOrder[] }, ApiError>(AVAILABLE_KEY, { refreshInterval: POLL_MS });
  const actions = useOrderAction();

  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-4 pb-16 pt-8 sm:px-6">
      <h1 className="font-serif text-4xl tracking-tight text-ink">Deliveries</h1>

      <section className="mt-8" aria-labelledby="my-deliveries">
        <h2 id="my-deliveries" className="font-sans text-xs font-semibold uppercase tracking-[0.18em] text-sage">
          Your deliveries
        </h2>
        <div className="mt-3 space-y-4">
          {!active.data ? (
            <div className="h-40 animate-pulse rounded-xl bg-surface" />
          ) : active.data.items.length === 0 ? (
            <p className="rounded-xl border border-dashed border-line px-5 py-8 text-center text-sm text-muted-ink">
              No active deliveries. Take an order from the list below.
            </p>
          ) : (
            active.data.items.map((order) => <ActiveDelivery key={order.id} order={order} actions={actions} />)
          )}
        </div>
      </section>

      <section className="mt-10" aria-labelledby="ready-orders">
        <h2 id="ready-orders" className="font-sans text-xs font-semibold uppercase tracking-[0.18em] text-sage">
          Ready for pickup
          {available.data && available.data.items.length > 0 && (
            <span className="ml-2 text-muted-ink">{available.data.items.length}</span>
          )}
        </h2>
        {!available.data ? (
          <div className="mt-3 h-24 animate-pulse rounded-xl bg-surface" />
        ) : available.data.items.length === 0 ? (
          <p className="mt-3 text-sm text-muted-ink">Nothing is waiting right now. The list refreshes on its own.</p>
        ) : (
          <ul className="mt-1 border-t border-line">
            {available.data.items.map((order) => (
              <AvailableOrder key={order.id} order={order} actions={actions} />
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
