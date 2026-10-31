"use client";

import Link from "next/link";
import { useState } from "react";
import useSWR from "swr";

import type { ApiError } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import { DELIVERY_METHOD_LABELS, ORDER_STATUS_LABELS } from "@/lib/order-labels";
import type { Page } from "@/types/api";
import type { AdminOrderRow, AdminRestaurantRow } from "@/types/admin";
import type { OrderStatus } from "@/types/orders";

const PAGE_SIZE = 20;
const POLL_MS = 15_000;
const STATUSES = Object.keys(ORDER_STATUS_LABELS) as OrderStatus[];
const ACTIVE: OrderStatus[] = ["pending_payment", "accepted", "preparing", "ready_for_pickup", "delivering"];
const dateTime = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

function StatusPill({ status }: { status: OrderStatus }) {
  const tone = ACTIVE.includes(status)
    ? status === "accepted"
      ? "bg-accent text-white"
      : "bg-saffron/25 text-ink"
    : status === "cancelled"
      ? "bg-surface text-accent-strong"
      : "bg-surface text-muted-ink";
  return <span className={`whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-medium ${tone}`}>{ORDER_STATUS_LABELS[status]}</span>;
}

/** All orders with filters; refreshes every 15 s so new orders appear on their own. */
export function OrdersBoard() {
  const [status, setStatus] = useState<OrderStatus | "">("");
  const [restaurantId, setRestaurantId] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [page, setPage] = useState(1);

  const params = new URLSearchParams({ page: String(page), per_page: String(PAGE_SIZE) });
  if (status) params.set("status", status);
  if (restaurantId) params.set("restaurant_id", restaurantId);
  if (dateFrom) params.set("date_from", dateFrom);
  if (dateTo) params.set("date_to", dateTo);
  const { data, error } = useSWR<Page<AdminOrderRow>, ApiError>(`/admin/orders?${params}`, {
    refreshInterval: POLL_MS,
    keepPreviousData: true,
  });
  const { data: restaurants } = useSWR<Page<AdminRestaurantRow>>("/admin/restaurants?per_page=50");

  const resetPage = <T,>(setter: (value: T) => void) => (value: T) => {
    setter(value);
    setPage(1);
  };
  const filterClass = "rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink outline-none focus:border-accent";

  return (
    <div>
      <h1 className="font-serif text-3xl text-ink">Orders</h1>

      <div className="mt-5 flex flex-wrap items-end gap-3">
        <label className="text-xs text-muted-ink">
          Status
          <select value={status} onChange={(e) => resetPage(setStatus)(e.target.value as OrderStatus | "")} className={`mt-1 block ${filterClass}`}>
            <option value="">All</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {ORDER_STATUS_LABELS[s]}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs text-muted-ink">
          Restaurant
          <select value={restaurantId} onChange={(e) => resetPage(setRestaurantId)(e.target.value)} className={`mt-1 block ${filterClass}`}>
            <option value="">All</option>
            {restaurants?.items.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs text-muted-ink">
          From
          <input type="date" value={dateFrom} onChange={(e) => resetPage(setDateFrom)(e.target.value)} className={`mt-1 block ${filterClass}`} />
        </label>
        <label className="text-xs text-muted-ink">
          To
          <input type="date" value={dateTo} onChange={(e) => resetPage(setDateTo)(e.target.value)} className={`mt-1 block ${filterClass}`} />
        </label>
        {(status || restaurantId || dateFrom || dateTo) && (
          <button
            type="button"
            onClick={() => {
              setStatus("");
              setRestaurantId("");
              setDateFrom("");
              setDateTo("");
              setPage(1);
            }}
            className="pb-2 text-sm text-accent-strong hover:underline"
          >
            Clear
          </button>
        )}
      </div>

      {error && !data ? (
        <p role="alert" className="mt-6 text-sm text-accent-strong">
          {error.details[0]?.message ?? error.message}
        </p>
      ) : !data ? (
        <div className="mt-6 h-64 animate-pulse rounded-xl bg-surface" aria-busy />
      ) : data.items.length === 0 ? (
        <p className="mt-6 rounded-xl border border-dashed border-line px-5 py-10 text-center text-sm text-muted-ink">
          No orders match these filters.
        </p>
      ) : (
        <div className="mt-5 overflow-x-auto rounded-xl border border-line">
          <table className="w-full min-w-[48rem] text-left text-sm">
            <thead className="bg-surface text-xs uppercase tracking-wider text-muted-ink">
              <tr>
                <th className="px-4 py-2.5 font-medium">Order</th>
                <th className="px-4 py-2.5 font-medium">Placed</th>
                <th className="px-4 py-2.5 font-medium">Restaurant</th>
                <th className="px-4 py-2.5 font-medium">Customer</th>
                <th className="px-4 py-2.5 font-medium">Delivery</th>
                <th className="px-4 py-2.5 text-right font-medium">Total</th>
                <th className="px-4 py-2.5 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line bg-card">
              {data.items.map((order) => (
                <tr key={order.id} className="hover:bg-surface/50">
                  <td className="px-4 py-2.5">
                    <Link href={`/admin/orders/${order.id}`} className="font-medium text-ink hover:text-accent-strong hover:underline">
                      #{order.id}
                    </Link>
                  </td>
                  <td className="whitespace-nowrap px-4 py-2.5 text-muted-ink">{dateTime.format(new Date(order.created_at))}</td>
                  <td className="px-4 py-2.5">{order.restaurant_name}</td>
                  <td className="px-4 py-2.5">{order.customer_name}</td>
                  <td className="px-4 py-2.5 text-muted-ink">
                    {DELIVERY_METHOD_LABELS[order.delivery_method].title}
                    {order.courier_name && <span className="block text-xs">{order.courier_name}</span>}
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums">
                    {formatPrice(order.total)}
                    <span className="block text-xs text-muted-ink">
                      {order.payment_method === "cash" ? "cash" : "card"} · {order.payment_status}
                    </span>
                  </td>
                  <td className="px-4 py-2.5">
                    <StatusPill status={order.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data && data.pages > 1 && (
        <div className="mt-4 flex items-center justify-end gap-3 text-sm">
          <button type="button" disabled={page <= 1} onClick={() => setPage(page - 1)} className="rounded-full border border-line px-3 py-1 disabled:opacity-40">
            Previous
          </button>
          <span className="text-muted-ink">
            Page {data.page} of {data.pages} · {data.total} orders
          </span>
          <button type="button" disabled={page >= data.pages} onClick={() => setPage(page + 1)} className="rounded-full border border-line px-3 py-1 disabled:opacity-40">
            Next
          </button>
        </div>
      )}
    </div>
  );
}
