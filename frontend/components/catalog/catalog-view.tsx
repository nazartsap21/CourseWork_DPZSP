"use client";

import { ChevronLeft, ChevronRight, SlidersHorizontal } from "lucide-react";
import { useState } from "react";
import useSWR from "swr";

import type { ApiError } from "@/lib/api";
import { restaurantsApiPath, SORT_OPTIONS, useCatalogFilters } from "@/lib/catalog-filters";
import { pluralize } from "@/lib/format";
import type { Page } from "@/types/api";
import type { RestaurantSort, RestaurantSummary } from "@/types/catalog";

import { FiltersPanel } from "./filters-panel";
import { RestaurantCard, RestaurantCardSkeleton } from "./restaurant-card";

export function CatalogView() {
  const { filters, update, clear, activeCount } = useCatalogFilters();
  const [filtersOpen, setFiltersOpen] = useState(false);
  // keepPreviousData: the old list stays (dimmed) while the new filter loads,
  // instead of the grid collapsing into skeletons on every click.
  const { data, error, isLoading, isValidating, mutate } = useSWR<Page<RestaurantSummary>, ApiError>(
    restaurantsApiPath(filters),
    { keepPreviousData: true },
  );

  return (
    <div className="lg:grid lg:grid-cols-[15.5rem_1fr] lg:gap-10">
      <aside className="mb-6 lg:mb-0">
        <button
          type="button"
          onClick={() => setFiltersOpen((open) => !open)}
          aria-expanded={filtersOpen}
          aria-controls="catalog-filters"
          className="flex w-full items-center justify-between rounded-lg border border-line bg-card px-4 py-2.5 text-sm font-medium text-ink lg:hidden"
        >
          <span className="inline-flex items-center gap-2">
            <SlidersHorizontal aria-hidden className="h-4 w-4" />
            Filters
          </span>
          {activeCount > 0 && <span className="rounded-full bg-accent px-2 text-xs text-white">{activeCount}</span>}
        </button>
        <div
          id="catalog-filters"
          className={`${filtersOpen ? "mt-4 block" : "hidden"} lg:sticky lg:top-6 lg:mt-0 lg:block`}
        >
          <FiltersPanel filters={filters} update={update} />
          {activeCount > 0 && (
            <button
              type="button"
              onClick={clear}
              className="mt-5 text-sm font-medium text-accent-strong underline-offset-4 hover:underline"
            >
              Clear filters
            </button>
          )}
        </div>
      </aside>

      <section aria-label="Restaurants" aria-busy={isLoading || isValidating}>
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-muted-ink" aria-live="polite">
            {data ? pluralize(data.total, "restaurant", "restaurants") : " "}
          </p>
          <label className="flex items-center gap-2 text-sm text-muted-ink">
            Sort by
            <select
              value={filters.sort}
              onChange={(e) => update({ sort: e.target.value as RestaurantSort })}
              className="rounded-lg border border-line bg-card px-3 py-1.5 text-sm text-ink outline-none focus:border-accent"
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        {error && !data ? (
          <div className="rounded-xl border border-line bg-card px-6 py-12 text-center">
            <p className="font-serif text-2xl text-ink">Couldn&apos;t load restaurants</p>
            <p className="mt-2 text-sm text-muted-ink">{error.message}</p>
            <button
              type="button"
              onClick={() => void mutate()}
              className="mt-5 rounded-full bg-accent px-5 py-2 text-sm font-semibold text-white hover:bg-accent-strong"
            >
              Try again
            </button>
          </div>
        ) : !data ? (
          <div className="grid gap-x-6 gap-y-10 sm:grid-cols-2 xl:grid-cols-3">
            {Array.from({ length: 6 }, (_, i) => (
              <RestaurantCardSkeleton key={i} />
            ))}
          </div>
        ) : data.items.length === 0 ? (
          <div className="rounded-xl border border-dashed border-line px-6 py-14 text-center">
            <p className="font-serif text-2xl text-ink">Nothing matches these filters</p>
            <p className="mt-2 text-sm text-muted-ink">Try a longer delivery time or another cuisine.</p>
            <button
              type="button"
              onClick={clear}
              className="mt-5 rounded-full border border-ink px-5 py-2 text-sm font-semibold text-ink hover:bg-ink hover:text-background"
            >
              Clear filters
            </button>
          </div>
        ) : (
          <>
            <div
              className={`grid gap-x-6 gap-y-10 transition-opacity sm:grid-cols-2 xl:grid-cols-3 ${
                isValidating ? "opacity-60" : ""
              }`}
            >
              {data.items.map((restaurant) => (
                <RestaurantCard key={restaurant.id} restaurant={restaurant} />
              ))}
            </div>
            {data.pages > 1 && (
              <nav aria-label="Pages" className="mt-12 flex items-center justify-center gap-4 text-sm">
                <button
                  type="button"
                  disabled={data.page <= 1}
                  onClick={() => update({ page: data.page - 1 })}
                  className="inline-flex items-center gap-1 rounded-full border border-line px-3 py-1.5 text-ink disabled:opacity-40"
                >
                  <ChevronLeft aria-hidden className="h-4 w-4" />
                  Previous
                </button>
                <span className="text-muted-ink">
                  Page {data.page} of {data.pages}
                </span>
                <button
                  type="button"
                  disabled={data.page >= data.pages}
                  onClick={() => update({ page: data.page + 1 })}
                  className="inline-flex items-center gap-1 rounded-full border border-line px-3 py-1.5 text-ink disabled:opacity-40"
                >
                  Next
                  <ChevronRight aria-hidden className="h-4 w-4" />
                </button>
              </nav>
            )}
          </>
        )}
      </section>
    </div>
  );
}
