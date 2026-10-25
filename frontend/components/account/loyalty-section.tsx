"use client";

import { Sparkles } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useState } from "react";
import useSWR from "swr";

import { ApiError, api } from "@/lib/api";
import { formatPrice, pluralize } from "@/lib/format";
import type { BonusTransaction, Loyalty } from "@/types/loyalty";

const dateFormat = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "long" });
const shortDate = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short" });

function transactionLabel(t: BonusTransaction): string {
  const order = t.order_id ? ` order #${t.order_id}` : " an order";
  switch (t.reason) {
    case "order_accrual":
      return `Earned for${order}`;
    case "order_redemption":
      return `Spent on${order}`;
    case "redemption_refund":
      return `Returned for cancelled${order}`;
    case "admin_adjustment":
      return "Adjustment by Forkful";
  }
}

/** Loyalty program in the account: card, points, progress to regular customer, history. */
export function LoyaltySection() {
  const { data: loyalty, error } = useSWR<Loyalty, ApiError>("/loyalty");
  const cancelledPayment = useSearchParams().get("premium") === "cancelled";
  const [buying, setBuying] = useState(false);
  const [buyError, setBuyError] = useState<string | null>(null);

  async function buyPremium() {
    setBuying(true);
    setBuyError(null);
    try {
      const { redirect_url } = await api.post<{ redirect_url: string }>("/loyalty/premium", {});
      // Same payment flow as orders: Stripe (or the mock) and back to the success page.
      window.location.assign(redirect_url);
    } catch (err) {
      if (!(err instanceof ApiError)) throw err;
      setBuyError(err.message);
      setBuying(false);
    }
  }

  if (error) {
    return (
      <p role="alert" className="text-sm text-accent-strong">
        {error.message}
      </p>
    );
  }
  if (!loyalty) {
    return <div className="h-48 animate-pulse rounded-xl bg-surface" aria-busy />;
  }

  const { rules } = loyalty;
  const progress = Math.min(loyalty.completed_orders / rules.regular_customer_threshold, 1);

  return (
    <div className="space-y-6">
      {cancelledPayment && (
        <p role="status" className="rounded-lg bg-surface px-4 py-3 text-sm text-ink">
          The premium card payment was cancelled. Nothing was charged.
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <div
          className={`rounded-xl p-5 ${loyalty.has_premium ? "bg-ink text-background" : "border border-line bg-card text-ink"}`}
        >
          <p className={`text-xs font-semibold uppercase tracking-[0.18em] ${loyalty.has_premium ? "text-saffron" : "text-sage"}`}>
            {loyalty.has_premium ? "Premium card" : "Standard card"}
          </p>
          <p className="mt-3 font-serif text-4xl tabular-nums">{loyalty.points_balance}</p>
          <p className={`text-sm ${loyalty.has_premium ? "text-background/70" : "text-muted-ink"}`}>
            {pluralize(loyalty.points_balance, "point", "points")} · worth{" "}
            {formatPrice(loyalty.points_balance * rules.point_value)}
          </p>
          {loyalty.has_premium && loyalty.premium_until && (
            <p className="mt-4 inline-flex items-center gap-1.5 text-sm">
              <Sparkles aria-hidden className="h-4 w-4 text-saffron" />
              Free delivery until {dateFormat.format(new Date(loyalty.premium_until))}
            </p>
          )}
        </div>

        <div className="rounded-xl bg-surface p-5">
          <p className="font-medium text-ink">
            {loyalty.is_regular
              ? `Regular customer: ${rules.regular_customer_discount_percent}% off every order`
              : `${pluralize(loyalty.orders_to_regular, "more order", "more orders")} to get ${rules.regular_customer_discount_percent}% off`}
          </p>
          <div
            className="mt-3 h-1.5 overflow-hidden rounded-full bg-background"
            role="progressbar"
            aria-label="Progress to regular customer"
            aria-valuemin={0}
            aria-valuemax={rules.regular_customer_threshold}
            aria-valuenow={Math.min(loyalty.completed_orders, rules.regular_customer_threshold)}
          >
            <div className={`h-full rounded-full ${loyalty.is_regular ? "bg-sage" : "bg-saffron"}`} style={{ width: `${progress * 100}%` }} />
          </div>
          <p className="mt-2 text-xs text-muted-ink">
            {loyalty.is_regular
              ? pluralize(loyalty.completed_orders, "delivered order", "delivered orders")
              : `${loyalty.completed_orders} of ${rules.regular_customer_threshold} delivered orders`}
          </p>
          <p className="mt-4 text-xs leading-relaxed text-muted-ink">
            Earn {rules.points_per_100_uah} points for every 100 ₴. Points cover up to{" "}
            {rules.max_points_redemption_percent}% of the dishes at checkout.
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-line px-5 py-4">
        <div>
          <p className="font-medium text-ink">
            {loyalty.has_premium ? "Extend your premium card" : "Premium card: free delivery on every order"}
          </p>
          <p className="text-sm text-muted-ink">
            {formatPrice(rules.premium_card_price)} for {rules.premium_card_days} days
            {loyalty.has_premium ? ", added to the current period" : ""}
          </p>
        </div>
        <button
          type="button"
          onClick={() => void buyPremium()}
          disabled={buying}
          className="rounded-full bg-accent px-5 py-2.5 text-sm font-semibold text-white hover:bg-accent-strong disabled:opacity-50"
        >
          {buying ? "Opening payment…" : loyalty.has_premium ? "Extend" : "Get premium"}
        </button>
        {buyError && (
          <p role="alert" className="w-full text-sm text-accent-strong">
            {buyError}
          </p>
        )}
      </div>

      <div>
        <h3 className="font-sans text-xs font-semibold uppercase tracking-[0.18em] text-sage">Points history</h3>
        {loyalty.transactions.length === 0 ? (
          <p className="mt-3 text-sm text-muted-ink">
            No points yet. You earn them when an order is delivered.{" "}
            <Link href="/" className="font-medium text-accent-strong hover:underline">
              Find something to eat
            </Link>
          </p>
        ) : (
          <ul className="mt-2 border-t border-line">
            {loyalty.transactions.map((t, index) => (
              <li key={`${t.created_at}-${index}`} className="flex items-baseline justify-between gap-4 border-b border-line py-2.5 text-sm">
                <span className="text-ink">
                  {transactionLabel(t)}
                  <span className="ml-2 text-xs text-muted-ink">{shortDate.format(new Date(t.created_at))}</span>
                </span>
                <span className={`font-medium tabular-nums ${t.delta > 0 ? "text-sage" : "text-ink"}`}>
                  {t.delta > 0 ? `+${t.delta}` : `−${-t.delta}`}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
