import { Star } from "lucide-react";

import { formatRating, pluralize } from "@/lib/format";
import type { PriceLevel } from "@/types/catalog";

export function RatingBadge({ rating, reviewCount }: { rating: number | null; reviewCount: number }) {
  if (rating === null) {
    return <span className="text-sm text-muted-ink">New</span>;
  }
  return (
    <span className="inline-flex items-center gap-1 text-sm font-medium text-ink">
      <Star aria-hidden className="h-3.5 w-3.5 fill-saffron text-saffron" />
      {formatRating(rating)}
      <span className="font-normal text-muted-ink">({reviewCount})</span>
      <span className="sr-only">{pluralize(reviewCount, "review", "reviews")}</span>
    </span>
  );
}

/** "₴₴₴" with the unused levels faded, so the scale is visible at a glance. */
export function PriceLevelMark({ level }: { level: PriceLevel | null }) {
  if (level === null) return null;
  return (
    <span aria-label={`Price level ${level} of 3`} className="tracking-wider">
      <span>{"₴".repeat(level)}</span>
      <span className="opacity-30">{"₴".repeat(3 - level)}</span>
    </span>
  );
}
