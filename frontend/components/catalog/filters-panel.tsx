"use client";

import useSWR from "swr";

import {
  type CatalogFilters,
  DELIVERY_TIME_OPTIONS,
  PRICE_LEVELS,
  RATING_OPTIONS,
  toggle,
} from "@/lib/catalog-filters";
import type { CuisineWithCount } from "@/types/catalog";

import { PriceLevelMark } from "./restaurant-meta";

function FilterGroup({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <fieldset className="border-t border-line pt-4 first:border-t-0 first:pt-0">
      <legend className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-sage">{title}</legend>
      {children}
    </fieldset>
  );
}

function Chip({
  active,
  onClick,
  children,
  label,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
  label?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      aria-label={label}
      className={`rounded-full border px-3 py-1.5 text-sm transition ${
        active
          ? "border-ink bg-ink text-background"
          : "border-line bg-card text-ink hover:border-muted-ink/50"
      }`}
    >
      {children}
    </button>
  );
}

export function FiltersPanel({
  filters,
  update,
}: {
  filters: CatalogFilters;
  update: (patch: Partial<CatalogFilters>) => void;
}) {
  const { data: cuisines, isLoading } = useSWR<{ items: CuisineWithCount[] }>("/cuisines");

  return (
    <div className="space-y-5">
      <FilterGroup title="Cuisine">
        <div className="flex flex-wrap gap-2">
          {isLoading &&
            Array.from({ length: 6 }, (_, i) => (
              <div key={i} className="h-8 w-20 animate-pulse rounded-full bg-surface" />
            ))}
          {cuisines?.items.map((cuisine) => (
            <Chip
              key={cuisine.id}
              active={filters.cuisine.includes(cuisine.id)}
              onClick={() => update({ cuisine: toggle(filters.cuisine, cuisine.id) })}
            >
              {cuisine.name}
              <span className="ml-1.5 text-xs opacity-60">{cuisine.restaurant_count}</span>
            </Chip>
          ))}
        </div>
      </FilterGroup>

      <FilterGroup title="Price">
        <div className="flex gap-2">
          {PRICE_LEVELS.map((level) => (
            <Chip
              key={level}
              label={`Price level ${level}`}
              active={filters.price_level.includes(level)}
              onClick={() => update({ price_level: toggle(filters.price_level, level) })}
            >
              <PriceLevelMark level={level} />
            </Chip>
          ))}
        </div>
      </FilterGroup>

      <FilterGroup title="Delivery time">
        <div className="flex flex-wrap gap-2">
          <Chip active={!filters.max_delivery_minutes} onClick={() => update({ max_delivery_minutes: null })}>
            Any
          </Chip>
          {DELIVERY_TIME_OPTIONS.map((minutes) => (
            <Chip
              key={minutes}
              active={filters.max_delivery_minutes === minutes}
              onClick={() => update({ max_delivery_minutes: minutes })}
            >
              Up to {minutes} min
            </Chip>
          ))}
        </div>
      </FilterGroup>

      <FilterGroup title="Rating">
        <div className="flex flex-wrap gap-2">
          <Chip active={!filters.min_rating} onClick={() => update({ min_rating: null })}>
            Any
          </Chip>
          {RATING_OPTIONS.map((rating) => (
            <Chip key={rating} active={filters.min_rating === rating} onClick={() => update({ min_rating: rating })}>
              {rating.toFixed(1)}+
            </Chip>
          ))}
        </div>
      </FilterGroup>
    </div>
  );
}
