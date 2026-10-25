import { Star } from "lucide-react";

import { formatRating, pluralize } from "@/lib/format";
import type { RestaurantDetails } from "@/types/catalog";

const STARS = [5, 4, 3, 2, 1];

export function RatingSummary({ restaurant }: { restaurant: RestaurantDetails }) {
  if (restaurant.rating === null) {
    return (
      <section aria-label="Rating" className="rounded-xl bg-surface px-5 py-4">
        <p className="font-medium text-ink">No reviews yet</p>
        <p className="mt-1 text-sm text-muted-ink">Customers can rate the restaurant after a delivered order.</p>
      </section>
    );
  }

  const max = Math.max(...Object.values(restaurant.rating_breakdown), 1);
  return (
    <section aria-label="Rating" className="rounded-xl bg-surface px-5 py-4">
      <div className="flex items-baseline gap-2">
        <span className="font-serif text-4xl text-ink">{formatRating(restaurant.rating)}</span>
        <Star aria-hidden className="h-5 w-5 fill-saffron text-saffron" />
        <a href="#reviews" className="text-sm text-muted-ink underline-offset-2 hover:text-ink hover:underline">
          {pluralize(restaurant.review_count, "review", "reviews")}
        </a>
      </div>
      <ul className="mt-3 space-y-1.5">
        {STARS.map((star) => {
          const count = restaurant.rating_breakdown[String(star)] ?? 0;
          return (
            <li key={star} className="flex items-center gap-2 text-xs text-muted-ink">
              <span className="w-3 text-right">{star}</span>
              <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-background">
                <span className="block h-full rounded-full bg-saffron" style={{ width: `${(count / max) * 100}%` }} />
              </span>
              <span className="w-4 text-right">{count}</span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
