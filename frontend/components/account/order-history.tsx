"use client";

import { ChevronRight, RotateCcw } from "lucide-react";
import Link from "next/link";
import useSWRInfinite from "swr/infinite";

import type { ApiError } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import { useReorder } from "@/lib/reorder";
import { ORDER_STATUS_LABELS } from "@/lib/order-labels";
import type { Page } from "@/types/api";
import type { OrderStatus, OrderSummary } from "@/types/orders";

const PAGE_SIZE = 10;
const dateFormat = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

const ACTIVE: OrderStatus[] = ["pending_payment", "accepted", "preparing", "ready_for_pickup", "delivering"];

function statusClass(status: OrderStatus): string {
  if (ACTIVE.includes(status)) return "bg-accent text-white";
  if (status === "cancelled") return "bg-background text-accent-strong";
  return "bg-surface text-muted-ink";
}

function itemsPreview(order: OrderSummary): string {
  return order.items.map((item) => (item.quantity > 1 ? `${item.quantity} × ${item.name}` : item.name)).join(", ");
}

// Page key for useSWRInfinite: stop once the last page has been loaded.
const pageKey = (index: number, previous: Page<OrderSummary> | null) =>
  previous && index >= previous.pages ? null : `/orders?page=${index + 1}&per_page=${PAGE_SIZE}`;

export function OrderHistory() {
  const { data, error, size, setSize, isLoading, isValidating } = useSWRInfinite<Page<OrderSummary>, ApiError>(pageKey);
  const orders = data?.flatMap((page) => page.items) ?? [];
  const total = data?.[0]?.total ?? 0;
  const hasMore = orders.length < total;
  const loadingMore = isValidating && size > (data?.length ?? 0);
  const { reorder, pendingId, errorFor } = useReorder();

  if (error) {
    return (
      <p role="alert" className="text-accent-strong">
        {error.message}
      </p>
    );
  }
  if (isLoading) {
    return (
      <div className="space-y-3" aria-busy>
        {Array.from({ length: 4 }, (_, i) => (
          <div key={i} className="h-20 animate-pulse rounded-xl bg-surface" />
        ))}
      </div>
    );
  }
  if (orders.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-line px-6 py-14 text-center">
        <p className="font-serif text-2xl text-ink">No orders yet</p>
        <p className="mt-2 text-sm text-muted-ink">Your first order will show up here.</p>
        <Link
          href="/"
          className="mt-5 inline-block rounded-full bg-accent px-5 py-2.5 text-sm font-semibold text-white hover:bg-accent-strong"
        >
          Browse restaurants
        </Link>
      </div>
    );
  }

  return (
    <>
      <ul className="border-t border-line">
        {orders.map((order) => (
          <li key={order.id} className="flex flex-wrap items-center gap-x-3 border-b border-line">
            <Link
              href={`/orders/${order.id}`}
              className="group flex min-w-0 flex-1 basis-64 items-center gap-4 py-4 transition hover:bg-surface/60 sm:px-2"
            >
              <div className="min-w-0 flex-1">
                <p className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                  <span className="font-serif text-lg text-ink">{order.restaurant.name}</span>
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${statusClass(order.status)}`}>
                    {ORDER_STATUS_LABELS[order.status]}
                  </span>
                </p>
                <p className="mt-1 truncate text-sm text-muted-ink">{itemsPreview(order)}</p>
                <p className="mt-0.5 text-xs text-muted-ink">
                  #{order.id} · {dateFormat.format(new Date(order.created_at))}
                </p>
              </div>
              <span className="shrink-0 font-medium tabular-nums text-ink">{formatPrice(order.total)}</span>
              <ChevronRight aria-hidden className="h-4 w-4 shrink-0 text-muted-ink group-hover:text-ink" />
            </Link>
            <button
              type="button"
              onClick={() => void reorder(order.id)}
              disabled={pendingId !== null}
              aria-label={`Order again from ${order.restaurant.name}`}
              className="mb-4 inline-flex items-center gap-1.5 rounded-full border border-line px-3 py-1.5 text-sm font-medium text-ink hover:border-muted-ink/50 disabled:opacity-50 sm:mb-0"
            >
              <RotateCcw aria-hidden className="h-3.5 w-3.5" />
              {pendingId === order.id ? "Adding…" : "Order again"}
            </button>
            {errorFor(order.id) && (
              <p role="alert" className="w-full pb-3 text-sm text-accent-strong">
                {errorFor(order.id)}
              </p>
            )}
          </li>
        ))}
      </ul>
      {hasMore && (
        <div className="mt-6 text-center">
          <button
            type="button"
            onClick={() => void setSize(size + 1)}
            disabled={loadingMore}
            className="rounded-full border border-ink px-5 py-2 text-sm font-semibold text-ink hover:bg-ink hover:text-background disabled:opacity-50"
          >
            {loadingMore ? "Loading…" : "Show more"}
          </button>
        </div>
      )}
    </>
  );
}
