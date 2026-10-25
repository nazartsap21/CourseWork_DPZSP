"use client";

import useSWR from "swr";

import type { RestaurantSummary } from "@/types/catalog";

import { api } from "./api";
import { useAuth } from "./auth";

const FAVORITES_KEY = "/favorites";

/** The customer's favorite restaurants, with an optimistic toggle. Empty for everyone else. */
export function useFavorites() {
  const { user } = useAuth();
  const isCustomer = user?.role === "customer";
  const { data, error, isLoading, mutate } = useSWR<{ items: RestaurantSummary[] }>(
    isCustomer ? FAVORITES_KEY : null,
  );
  const items = data?.items ?? [];

  const isFavorite = (restaurantId: number) => items.some((r) => r.id === restaurantId);

  /** Adds or removes; the heart changes immediately, the list re-syncs from the server. */
  async function toggle(restaurant: RestaurantSummary) {
    const remove = isFavorite(restaurant.id);
    const optimistic = remove ? items.filter((r) => r.id !== restaurant.id) : [restaurant, ...items];
    await mutate(
      async () => {
        await (remove ? api.delete(`/favorites/${restaurant.id}`) : api.put(`/favorites/${restaurant.id}`));
        return undefined;
      },
      { optimisticData: { items: optimistic }, populateCache: false, revalidate: true, rollbackOnError: true },
    );
  }

  return { items, isLoading: isCustomer && isLoading, error, isFavorite, toggle, enabled: isCustomer };
}
