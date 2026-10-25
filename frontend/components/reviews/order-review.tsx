"use client";

import { useState } from "react";
import { useSWRConfig } from "swr";

import { ApiError, api } from "@/lib/api";
import type { Order } from "@/types/orders";
import type { OwnReview } from "@/types/reviews";

import { StarInput, Stars } from "./stars";

const MAX_TEXT = 1000;

/** On a delivered order: the review form, or the customer's review once it's sent. */
export function OrderReview({ order }: { order: Order }) {
  const { mutate } = useSWRConfig();
  const [rating, setRating] = useState(0);
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (order.review) {
    return (
      <section aria-labelledby="your-review" className="rounded-xl border border-line bg-card p-5">
        <h2 id="your-review" className="font-sans text-xs font-semibold uppercase tracking-[0.18em] text-sage">
          Your review
        </h2>
        <div className="mt-3">
          <Stars rating={order.review.rating} />
        </div>
        {order.review.text && <p className="mt-2 text-sm leading-relaxed text-ink">{order.review.text}</p>}
      </section>
    );
  }
  if (!order.can_review) return null;

  async function submit() {
    setSubmitting(true);
    setError(null);
    try {
      const review = await api.post<OwnReview>(`/orders/${order.id}/review`, { rating, text });
      await mutate(`/orders/${order.id}`, { ...order, review, can_review: false }, { revalidate: false });
      // The restaurant's rating and review list change too.
      void mutate(`/restaurants/${order.restaurant.id}`);
    } catch (err) {
      if (!(err instanceof ApiError)) throw err;
      setError(err.details[0]?.message ?? err.message);
      setSubmitting(false);
    }
  }

  return (
    <section aria-labelledby="rate-order" className="rounded-xl border border-line bg-card p-5">
      <h2 id="rate-order" className="font-serif text-2xl text-ink">
        How was {order.restaurant.name}?
      </h2>
      <p className="mt-1 text-sm text-muted-ink">Your rating helps other people in Lviv choose.</p>
      <form
        className="mt-4 space-y-4"
        onSubmit={(event) => {
          event.preventDefault();
          void submit();
        }}
      >
        <StarInput value={rating} onChange={setRating} />
        <div>
          <label htmlFor="review-text" className="mb-1.5 block text-sm font-medium text-ink">
            What did you like or miss? <span className="font-normal text-muted-ink">(optional)</span>
          </label>
          <textarea
            id="review-text"
            value={text}
            onChange={(e) => setText(e.target.value.slice(0, MAX_TEXT))}
            rows={3}
            className="w-full rounded-lg border border-line bg-background px-3 py-2.5 text-ink outline-none transition placeholder:text-muted-ink/60 focus:border-accent focus:ring-2 focus:ring-accent/30"
            placeholder="The pizza arrived hot, the crust was still crisp."
          />
          <p className="mt-1 text-right text-xs text-muted-ink">
            {text.length}/{MAX_TEXT}
          </p>
        </div>
        {error && (
          <p role="alert" className="text-sm text-accent-strong">
            {error}
          </p>
        )}
        <button
          type="submit"
          disabled={rating === 0 || submitting}
          className="rounded-full bg-accent px-5 py-2.5 text-sm font-semibold text-white hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? "Sending…" : rating === 0 ? "Choose a rating" : "Send review"}
        </button>
      </form>
    </section>
  );
}
