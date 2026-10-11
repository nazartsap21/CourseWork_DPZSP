import { Clock } from "lucide-react";
import Link from "next/link";

import { formatDeliveryWindow, formatPrice } from "@/lib/format";
import type { RestaurantSummary } from "@/types/catalog";

import { RestaurantCover } from "./restaurant-cover";
import { PriceLevelMark, RatingBadge } from "./restaurant-meta";

export function RestaurantCard({ restaurant }: { restaurant: RestaurantSummary }) {
  const cuisines = restaurant.cuisines.map((c) => c.name).join(", ");

  return (
    <Link href={`/restaurants/${restaurant.id}`} className="group block">
      <RestaurantCover
        id={restaurant.id}
        name={restaurant.name}
        imageUrl={restaurant.image_url}
        label={restaurant.cuisines[0]?.name}
        className="aspect-[16/10] rounded-xl transition duration-300 group-hover:brightness-95"
      />
      <div className="mt-3 flex items-start justify-between gap-3">
        <h2 className="font-serif text-xl leading-tight text-ink decoration-accent/60 underline-offset-4 group-hover:underline">
          {restaurant.name}
        </h2>
        <RatingBadge rating={restaurant.rating} reviewCount={restaurant.review_count} />
      </div>
      <p className="mt-1 text-sm text-muted-ink">
        {cuisines}
        {restaurant.price_level && (
          <>
            <span className="mx-1.5">·</span>
            <PriceLevelMark level={restaurant.price_level} />
          </>
        )}
      </p>
      <p className="mt-2 flex items-center gap-3 text-sm text-ink">
        <span className="inline-flex items-center gap-1.5">
          <Clock aria-hidden className="h-3.5 w-3.5 text-sage" />
          {formatDeliveryWindow(restaurant.delivery_minutes_min, restaurant.delivery_minutes_max)}
        </span>
        <span className="text-muted-ink">Min. order {formatPrice(restaurant.min_order_amount)}</span>
      </p>
    </Link>
  );
}

export function RestaurantCardSkeleton() {
  return (
    <div aria-hidden>
      <div className="aspect-[16/10] animate-pulse rounded-xl bg-surface" />
      <div className="mt-3 h-6 w-2/3 animate-pulse rounded bg-surface" />
      <div className="mt-2 h-4 w-1/2 animate-pulse rounded bg-surface" />
      <div className="mt-2 h-4 w-3/4 animate-pulse rounded bg-surface" />
    </div>
  );
}
