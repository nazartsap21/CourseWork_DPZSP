"use client";

import useSWRInfinite from "swr/infinite";

import type { ApiError } from "@/lib/api";
import { pluralize } from "@/lib/format";
import type { Page } from "@/types/api";
import type { PublicReview } from "@/types/reviews";

import { Stars } from "./stars";

const PAGE_SIZE = 5;
const dateFormat = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "long", year: "numeric" });

/** Customer reviews on the restaurant page, newest first, five at a time. */
export function ReviewsList({ restaurantId }: { restaurantId: number }) {
  const { data, error, size, setSize, isLoading, isValidating } = useSWRInfinite<Page<PublicReview>, ApiError>(
    (index, previous: Page<PublicReview> | null) =>
      previous && index >= previous.pages
        ? null
        : `/restaurants/${restaurantId}/reviews?page=${index + 1}&per_page=${PAGE_SIZE}`,
  );
  const reviews = data?.flatMap((page) => page.items) ?? [];
  const total = data?.[0]?.total ?? 0;
  const loadingMore = isValidating && size > (data?.length ?? 0);

  return (
    <section id="reviews" aria-labelledby="reviews-title" className="scroll-mt-16">
      <h2 id="reviews-title" className="font-serif text-2xl text-ink">
        Reviews
        {total > 0 && <span className="ml-2 align-middle text-sm font-normal text-muted-ink">{total}</span>}
      </h2>
      {error ? (
        <p role="alert" className="mt-3 text-sm text-accent-strong">
          {error.message}
        </p>
      ) : isLoading ? (
        <div className="mt-4 space-y-3" aria-busy>
          {Array.from({ length: 2 }, (_, i) => (
            <div key={i} className="h-20 animate-pulse rounded-lg bg-surface" />
          ))}
        </div>
      ) : reviews.length === 0 ? (
        <p className="mt-3 text-sm text-muted-ink">
          No reviews yet. Customers can rate the restaurant after a delivered order.
        </p>
      ) : (
        <>
          <ul className="mt-3 grid gap-x-10 md:grid-cols-2">
            {reviews.map((review) => (
              <li key={review.id} className="border-b border-line py-4">
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                  <Stars rating={review.rating} size="h-3.5 w-3.5" />
                  <span className="text-sm font-medium text-ink">{review.author}</span>
                  <span className="text-xs text-muted-ink">{dateFormat.format(new Date(review.created_at))}</span>
                </div>
                {review.text && <p className="mt-2 text-sm leading-relaxed text-ink">{review.text}</p>}
              </li>
            ))}
          </ul>
          {reviews.length < total && (
            <button
              type="button"
              onClick={() => void setSize(size + 1)}
              disabled={loadingMore}
              className="mt-5 rounded-full border border-ink px-5 py-2 text-sm font-semibold text-ink hover:bg-ink hover:text-background disabled:opacity-50"
            >
              {loadingMore ? "Loading…" : `Show more (${pluralize(total - reviews.length, "review", "reviews")} left)`}
            </button>
          )}
        </>
      )}
    </section>
  );
}
