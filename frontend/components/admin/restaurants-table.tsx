"use client";

import { Plus, Search } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import useSWR from "swr";

import { ApiError, api } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import { useDebounced } from "@/lib/use-debounced";
import type { Page } from "@/types/api";
import type { AdminRestaurantRow } from "@/types/admin";

const PAGE_SIZE = 20;
type ActiveFilter = "all" | "true" | "false";

export function RestaurantsTable() {
  const [query, setQuery] = useState("");
  const [active, setActive] = useState<ActiveFilter>("all");
  const [page, setPage] = useState(1);
  const debouncedQuery = useDebounced(query, 300);
  const params = new URLSearchParams({ page: String(page), per_page: String(PAGE_SIZE) });
  if (debouncedQuery) params.set("q", debouncedQuery);
  if (active !== "all") params.set("active", active);
  const key = `/admin/restaurants?${params}`;
  const { data, error, mutate } = useSWR<Page<AdminRestaurantRow>, ApiError>(key, { keepPreviousData: true });
  const [toggling, setToggling] = useState<number | null>(null);

  async function toggleActive(row: AdminRestaurantRow) {
    setToggling(row.id);
    try {
      await api.patch(`/admin/restaurants/${row.id}`, { is_active: !row.is_active });
      await mutate();
    } finally {
      setToggling(null);
    }
  }

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="font-serif text-3xl text-ink">Restaurants</h1>
        <Link
          href="/admin/restaurants/new"
          className="inline-flex items-center gap-1.5 rounded-full bg-accent px-4 py-2 text-sm font-semibold text-white hover:bg-accent-strong"
        >
          <Plus aria-hidden className="h-4 w-4" />
          New restaurant
        </Link>
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-3">
        <label className="relative flex-1 basis-56">
          <span className="sr-only">Search by name</span>
          <Search aria-hidden className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-ink" />
          <input
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setPage(1);
            }}
            placeholder="Search by name"
            className="w-full rounded-lg border border-line bg-card py-2 pl-9 pr-3 text-sm text-ink outline-none focus:border-accent"
          />
        </label>
        <select
          value={active}
          onChange={(e) => {
            setActive(e.target.value as ActiveFilter);
            setPage(1);
          }}
          aria-label="Status"
          className="rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink outline-none focus:border-accent"
        >
          <option value="all">All statuses</option>
          <option value="true">Active</option>
          <option value="false">Inactive</option>
        </select>
      </div>

      {error && !data ? (
        <p role="alert" className="mt-6 text-sm text-accent-strong">
          {error.message}
        </p>
      ) : !data ? (
        <div className="mt-6 h-64 animate-pulse rounded-xl bg-surface" aria-busy />
      ) : data.items.length === 0 ? (
        <p className="mt-6 rounded-xl border border-dashed border-line px-5 py-10 text-center text-sm text-muted-ink">
          No restaurants match. Try another name or status.
        </p>
      ) : (
        <div className="mt-5 overflow-x-auto rounded-xl border border-line">
          <table className="w-full min-w-[44rem] text-left text-sm">
            <thead className="bg-surface text-xs uppercase tracking-wider text-muted-ink">
              <tr>
                <th className="px-4 py-2.5 font-medium">Name</th>
                <th className="px-4 py-2.5 font-medium">Cuisines</th>
                <th className="px-4 py-2.5 text-right font-medium">Dishes</th>
                <th className="px-4 py-2.5 text-right font-medium">Prep</th>
                <th className="px-4 py-2.5 text-right font-medium">Min. order</th>
                <th className="px-4 py-2.5 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line bg-card">
              {data.items.map((row) => (
                <tr key={row.id} className={row.is_active ? "" : "text-muted-ink"}>
                  <td className="px-4 py-2.5">
                    <Link href={`/admin/restaurants/${row.id}`} className="font-medium text-ink hover:text-accent-strong hover:underline">
                      {row.name}
                    </Link>
                    <span className="block text-xs text-muted-ink">{row.address}</span>
                  </td>
                  <td className="px-4 py-2.5">{row.cuisines.map((c) => c.name).join(", ")}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{row.dish_count}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{row.avg_prep_minutes} min</td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{formatPrice(row.min_order_amount)}</td>
                  <td className="px-4 py-2.5">
                    <button
                      type="button"
                      role="switch"
                      aria-checked={row.is_active}
                      aria-label={`${row.name} is ${row.is_active ? "active" : "inactive"}`}
                      disabled={toggling === row.id}
                      onClick={() => void toggleActive(row)}
                      className={`rounded-full px-2.5 py-1 text-xs font-medium transition disabled:opacity-50 ${
                        row.is_active ? "bg-sage text-white" : "bg-surface text-muted-ink hover:text-ink"
                      }`}
                    >
                      {row.is_active ? "Active" : "Inactive"}
                    </button>
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
            Page {data.page} of {data.pages}
          </span>
          <button type="button" disabled={page >= data.pages} onClick={() => setPage(page + 1)} className="rounded-full border border-line px-3 py-1 disabled:opacity-40">
            Next
          </button>
        </div>
      )}
    </div>
  );
}
