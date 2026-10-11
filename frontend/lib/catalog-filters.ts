"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo } from "react";

import type { PriceLevel, RestaurantSort } from "@/types/catalog";

// The URL is the single source of truth for catalog filters, so a filtered
// view survives reload and can be shared as a link. Param names match the API.

export interface CatalogFilters {
  cuisine: number[];
  price_level: PriceLevel[];
  max_delivery_minutes: number | null;
  min_rating: number | null;
  sort: RestaurantSort;
  page: number;
}

export const DEFAULT_SORT: RestaurantSort = "rating";
export const CATALOG_PAGE_SIZE = 12;

export const SORT_OPTIONS: { value: RestaurantSort; label: string }[] = [
  { value: "rating", label: "Top rated" },
  { value: "delivery_time", label: "Fastest delivery" },
  { value: "price", label: "Lowest price" },
];
export const PRICE_LEVELS: PriceLevel[] = [1, 2, 3];
export const DELIVERY_TIME_OPTIONS = [40, 50];
export const RATING_OPTIONS = [4, 4.5];

function positiveInts(values: string[]): number[] {
  return values
    .flatMap((value) => value.split(","))
    .map(Number)
    .filter((n) => Number.isInteger(n) && n > 0);
}

function positiveNumber(value: string | null): number | null {
  const n = Number(value);
  return value && Number.isFinite(n) && n > 0 ? n : null;
}

// Invalid values are dropped instead of being sent on, so a hand-edited URL
// shows a sensible list rather than a validation error.
export function parseFilters(params: URLSearchParams): CatalogFilters {
  const sort = params.get("sort");
  return {
    cuisine: positiveInts(params.getAll("cuisine")),
    price_level: positiveInts(params.getAll("price_level")).filter((n): n is PriceLevel =>
      PRICE_LEVELS.includes(n as PriceLevel),
    ),
    max_delivery_minutes: positiveNumber(params.get("max_delivery_minutes")),
    min_rating: positiveNumber(params.get("min_rating")),
    sort: SORT_OPTIONS.some((o) => o.value === sort) ? (sort as RestaurantSort) : DEFAULT_SORT,
    page: positiveNumber(params.get("page")) ?? 1,
  };
}

/** Serializes filters, leaving defaults out to keep URLs short. */
export function filtersToQuery(filters: CatalogFilters): URLSearchParams {
  const query = new URLSearchParams();
  if (filters.cuisine.length) query.set("cuisine", filters.cuisine.join(","));
  if (filters.price_level.length) query.set("price_level", filters.price_level.join(","));
  if (filters.max_delivery_minutes) query.set("max_delivery_minutes", String(filters.max_delivery_minutes));
  if (filters.min_rating) query.set("min_rating", String(filters.min_rating));
  if (filters.sort !== DEFAULT_SORT) query.set("sort", filters.sort);
  if (filters.page > 1) query.set("page", String(filters.page));
  return query;
}

export function restaurantsApiPath(filters: CatalogFilters): string {
  const query = filtersToQuery(filters);
  query.set("per_page", String(CATALOG_PAGE_SIZE));
  return `/restaurants?${query}`;
}

export function countActiveFilters(filters: CatalogFilters): number {
  return (
    filters.cuisine.length +
    filters.price_level.length +
    (filters.max_delivery_minutes ? 1 : 0) +
    (filters.min_rating ? 1 : 0)
  );
}

export function useCatalogFilters() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const filters = useMemo(() => parseFilters(new URLSearchParams(searchParams)), [searchParams]);

  const navigate = useCallback(
    (next: CatalogFilters) => {
      const query = filtersToQuery(next).toString();
      router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
    },
    [router, pathname],
  );

  /** Any filter change returns to page 1; pass `page` explicitly to paginate. */
  const update = useCallback(
    (patch: Partial<CatalogFilters>) => navigate({ ...filters, page: 1, ...patch }),
    [filters, navigate],
  );

  const clear = useCallback(() => navigate({ ...parseFilters(new URLSearchParams()), sort: filters.sort }), [
    filters.sort,
    navigate,
  ]);

  return { filters, update, clear, activeCount: countActiveFilters(filters) };
}

export function toggle<T>(list: T[], value: T): T[] {
  return list.includes(value) ? list.filter((item) => item !== value) : [...list, value];
}
