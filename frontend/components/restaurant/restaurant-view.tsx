"use client";

import { ArrowLeft, MapPin } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo } from "react";
import useSWR from "swr";

import { OrderBar } from "@/components/cart/order-bar";
import { RestaurantCover } from "@/components/catalog/restaurant-cover";
import { PriceLevelMark } from "@/components/catalog/restaurant-meta";
import type { ApiError } from "@/lib/api";
import type { CartRestaurant } from "@/lib/cart-store";
import { formatDeliveryWindow, formatPrice } from "@/lib/format";
import type { Menu, RestaurantDetails } from "@/types/catalog";

import { MenuSections, MenuSkeleton } from "./menu-sections";
import { RatingSummary } from "./rating-summary";

function Stat({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="border-l border-line pl-4 first:border-l-0 first:pl-0">
      <dt className="text-xs uppercase tracking-[0.14em] text-muted-ink">{label}</dt>
      <dd className="mt-1 font-medium text-ink">{children}</dd>
    </div>
  );
}

export function RestaurantView({ restaurantId }: { restaurantId: number }) {
  const valid = Number.isInteger(restaurantId) && restaurantId > 0;
  const { data: restaurant, error } = useSWR<RestaurantDetails, ApiError>(
    valid ? `/restaurants/${restaurantId}` : null,
  );
  const { data: menu, error: menuError } = useSWR<Menu, ApiError>(
    valid ? `/restaurants/${restaurantId}/menu` : null,
  );

  const cartRestaurant = useMemo<CartRestaurant | null>(
    () =>
      restaurant
        ? { id: restaurant.id, name: restaurant.name, min_order_amount: restaurant.min_order_amount }
        : null,
    [restaurant],
  );

  useEffect(() => {
    if (restaurant) document.title = `${restaurant.name} · Forkful`;
  }, [restaurant]);

  if (!valid || error?.status === 404) {
    return (
      <main className="mx-auto w-full max-w-xl flex-1 px-4 py-20 text-center">
        <h1 className="font-serif text-4xl text-ink">Restaurant not found</h1>
        <p className="mt-3 text-muted-ink">It may have closed or stopped taking orders.</p>
        <Link
          href="/"
          className="mt-6 inline-block rounded-full bg-accent px-5 py-2.5 text-sm font-semibold text-white hover:bg-accent-strong"
        >
          See all restaurants
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-4 pb-28 pt-6 sm:px-6 lg:px-8">
      <Link href="/" className="inline-flex items-center gap-1.5 text-sm text-muted-ink hover:text-ink">
        <ArrowLeft aria-hidden className="h-4 w-4" />
        All restaurants
      </Link>

      {error ? (
        <p role="alert" className="mt-10 text-accent-strong">
          {error.message}
        </p>
      ) : !restaurant ? (
        <HeaderSkeleton />
      ) : (
        <header className="mt-5 grid gap-8 lg:grid-cols-[1fr_20rem]">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-sage">
              {restaurant.cuisines.map((c) => c.name).join(" · ")}
            </p>
            <h1 className="mt-2 font-serif text-4xl leading-tight tracking-tight text-ink sm:text-5xl">
              {restaurant.name}
            </h1>
            <p className="mt-3 max-w-2xl text-lg text-muted-ink">{restaurant.description}</p>
            <p className="mt-3 inline-flex items-center gap-1.5 text-sm text-muted-ink">
              <MapPin aria-hidden className="h-4 w-4 text-sage" />
              {restaurant.address}
            </p>
            <dl className="mt-6 flex flex-wrap gap-y-4">
              <Stat label="Delivery">
                {formatDeliveryWindow(restaurant.delivery_minutes_min, restaurant.delivery_minutes_max)}
              </Stat>
              <Stat label="Min. order">{formatPrice(restaurant.min_order_amount)}</Stat>
              {restaurant.price_level && (
                <Stat label="Price">
                  <PriceLevelMark level={restaurant.price_level} />
                </Stat>
              )}
            </dl>
          </div>
          <div className="space-y-5">
            <RestaurantCover
              id={restaurant.id}
              name={restaurant.name}
              imageUrl={restaurant.image_url}
              className="hidden aspect-[4/3] rounded-xl lg:block"
              initialClassName="text-9xl"
            />
            <RatingSummary restaurant={restaurant} />
          </div>
        </header>
      )}

      <div className="mt-10">
        {menuError ? (
          <p role="alert" className="text-accent-strong">
            Couldn&apos;t load the menu. {menuError.message}
          </p>
        ) : !menu ? (
          <MenuSkeleton />
        ) : (
          <MenuSections menu={menu} restaurant={cartRestaurant} />
        )}
      </div>
      <OrderBar restaurantId={restaurantId} />
    </main>
  );
}

function HeaderSkeleton() {
  return (
    <div className="mt-5 grid gap-8 lg:grid-cols-[1fr_20rem]" aria-hidden>
      <div className="space-y-3">
        <div className="h-3 w-32 animate-pulse rounded bg-surface" />
        <div className="h-12 w-2/3 animate-pulse rounded-lg bg-surface" />
        <div className="h-5 w-full max-w-xl animate-pulse rounded bg-surface" />
        <div className="h-4 w-48 animate-pulse rounded bg-surface" />
      </div>
      <div className="hidden aspect-[4/3] animate-pulse rounded-xl bg-surface lg:block" />
    </div>
  );
}
