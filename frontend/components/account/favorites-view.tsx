"use client";

import Link from "next/link";

import { RestaurantCard, RestaurantCardSkeleton } from "@/components/catalog/restaurant-card";
import { useFavorites } from "@/lib/favorites";

export function FavoritesView() {
  const { items, isLoading, error } = useFavorites();

  if (error) {
    return (
      <p role="alert" className="text-accent-strong">
        {error.message}
      </p>
    );
  }
  if (isLoading) {
    return (
      <div className="grid gap-x-6 gap-y-10 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 3 }, (_, i) => (
          <RestaurantCardSkeleton key={i} />
        ))}
      </div>
    );
  }
  if (items.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-line px-6 py-14 text-center">
        <p className="font-serif text-2xl text-ink">No favorites yet</p>
        <p className="mt-2 text-sm text-muted-ink">Tap “Save” on a restaurant page to keep it here.</p>
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
    <div className="grid gap-x-6 gap-y-10 sm:grid-cols-2 lg:grid-cols-3">
      {items.map((restaurant) => (
        <RestaurantCard key={restaurant.id} restaurant={restaurant} />
      ))}
    </div>
  );
}
