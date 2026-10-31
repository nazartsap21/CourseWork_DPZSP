"use client";

import Link from "next/link";
import useSWR from "swr";

import type { ApiError } from "@/lib/api";
import type { AdminRestaurant } from "@/types/admin";

import { DishesManager } from "./dishes-manager";
import { RestaurantForm } from "./restaurant-form";

export function RestaurantEditor({ restaurantId }: { restaurantId: number }) {
  const { data: restaurant, error } = useSWR<AdminRestaurant, ApiError>(`/admin/restaurants/${restaurantId}`);

  return (
    <div className="max-w-4xl space-y-10">
      <div>
        <Link href="/admin/restaurants" className="text-sm text-muted-ink hover:text-ink">
          ← Restaurants
        </Link>
        <div className="mt-2 flex flex-wrap items-baseline gap-3">
          <h1 className="font-serif text-3xl text-ink">{restaurant?.name ?? "Restaurant"}</h1>
          {restaurant && (
            <Link href={`/restaurants/${restaurant.id}`} className="text-sm text-accent-strong hover:underline">
              {restaurant.is_active ? "View in catalog" : "Hidden from customers"}
            </Link>
          )}
        </div>
      </div>
      {error ? (
        <p role="alert" className="text-accent-strong">
          {error.message}
        </p>
      ) : !restaurant ? (
        <div className="h-96 animate-pulse rounded-xl bg-surface" aria-busy />
      ) : (
        <>
          {/* Keyed by id so the form resets when switching restaurants. */}
          <RestaurantForm key={restaurant.id} restaurant={restaurant} />
          <div className="border-t border-line pt-8">
            <DishesManager restaurantId={restaurant.id} />
          </div>
        </>
      )}
    </div>
  );
}
