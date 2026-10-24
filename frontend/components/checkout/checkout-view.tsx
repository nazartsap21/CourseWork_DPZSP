"use client";

import { ArrowLeft, Banknote, CreditCard, MapPin } from "lucide-react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import useSWR from "swr";

import { FormField } from "@/components/form-field";
import { ApiError, api } from "@/lib/api";
import { useCart } from "@/lib/cart";
import { formatPrice, pluralize } from "@/lib/format";
import { useQuote } from "@/lib/quotes";
import { useDebounced } from "@/lib/use-debounced";
import { useHydrated } from "@/lib/use-hydrated";
import type { RestaurantDetails } from "@/types/catalog";
import type { CheckoutPayload, DeliveryMethod, PlacedOrder, Quote, QuotePayload } from "@/types/orders";

import type { MapPoint } from "./delivery-map";
import { MethodSelector } from "./method-selector";
import { OrderSummary } from "./order-summary";

// Leaflet needs `window`; load the map only in the browser.
const DeliveryMap = dynamic(() => import("./delivery-map"), {
  ssr: false,
  loading: () => <div className="h-full w-full animate-pulse bg-surface" />,
});

type OnlineOrCash = "stripe" | "cash";

function Section({ step, title, children }: { step: number; title: string; children: React.ReactNode }) {
  return (
    <section className="border-t border-line pt-6 first:border-t-0 first:pt-0">
      <h2 className="flex items-baseline gap-3 font-serif text-2xl text-ink">
        <span className="font-sans text-sm font-semibold text-sage">{step}</span>
        {title}
      </h2>
      <div className="mt-4">{children}</div>
    </section>
  );
}

function withoutKey(errors: Record<string, string>, key: string): Record<string, string> {
  return Object.fromEntries(Object.entries(errors).filter(([field]) => field !== key));
}

function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return (
    <p role="alert" className="mt-2 text-sm text-accent-strong">
      {message}
    </p>
  );
}

export function CheckoutView() {
  const hydrated = useHydrated();
  const router = useRouter();
  const { cart, clear } = useCart();
  const restaurantId = cart.restaurant?.id ?? null;

  const [method, setMethod] = useState<DeliveryMethod>("standard");
  const [point, setPoint] = useState<MapPoint | null>(null);
  const [address, setAddress] = useState("");
  const [note, setNote] = useState("");
  const [payment, setPayment] = useState<OnlineOrCash>("stripe");
  const [points, setPoints] = useState(0);
  const debouncedPoints = useDebounced(points, 300);
  const [submitErrors, setSubmitErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  // Set once the order exists and the browser is leaving for payment or the order page.
  const [leaving, setLeaving] = useState<"payment" | "order" | null>(null);

  const { data: restaurant } = useSWR<RestaurantDetails, ApiError>(
    restaurantId ? `/restaurants/${restaurantId}` : null,
  );

  const base = useMemo(() => {
    if (!restaurantId || cart.items.length === 0) return null;
    return {
      restaurant_id: restaurantId,
      items: cart.items.map((item) => ({ dish_id: item.dish_id, quantity: item.quantity })),
      ...(point ? { delivery_lat: point.lat, delivery_lng: point.lng } : {}),
    };
  }, [restaurantId, cart.items, point]);

  // One quote per method (no points) for the option tiles...
  const standard = useQuote(base && { ...base, delivery_method: "standard" });
  const express = useQuote(base && { ...base, delivery_method: "express" });
  const pickup = useQuote(base && { ...base, delivery_method: "pickup" });
  // ...and the full one for the summary. With 0 points it equals a tile's key, so SWR reuses it.
  const summaryPayload: QuotePayload | null = base && {
    ...base,
    delivery_method: method,
    ...(debouncedPoints > 0 ? { bonus_points: debouncedPoints } : {}),
  };
  const summary = useQuote(summaryPayload);
  const quote: Quote | undefined = summary.data;
  const methodQuotes = { standard: standard.data, express: express.data, pickup: pickup.data };

  const issue = quote?.validation_error ?? null;
  const fieldError = (field: string) =>
    submitErrors[field] ?? (issue?.field === field ? issue.message : undefined);
  const generalIssue =
    issue && !["delivery_point", "bonus_points", "delivery_address"].includes(issue.field ?? "") ? issue : null;

  const isPickup = method === "pickup";
  const maxPoints = quote?.loyalty.max_redeemable_points ?? 0;
  const pointsLoading = points !== debouncedPoints || summary.isValidating;
  const canSubmit = Boolean(quote) && !issue && !submitting && !pointsLoading;

  async function placeOrder() {
    if (!summaryPayload) return;
    setSubmitting(true);
    setSubmitErrors({});
    setFormError(null);
    const payload: CheckoutPayload = {
      ...summaryPayload,
      payment_method: payment,
      ...(isPickup ? {} : { delivery_address: address, delivery_note: note }),
    };
    try {
      const order = await api.post<PlacedOrder>("/orders", payload);
      // The order exists now, so the cart can go; `leaving` keeps this page from
      // flashing "nothing to check out" while the browser navigates away.
      setLeaving(order.payment_redirect_url ? "payment" : "order");
      clear();
      if (order.payment_redirect_url) {
        // Stripe Checkout is another site: full navigation, not a router push.
        window.location.assign(order.payment_redirect_url);
      } else {
        router.push(`/orders/${order.id}`);
      }
    } catch (error) {
      if (!(error instanceof ApiError)) throw error;
      if (error.details.length > 0) {
        setSubmitErrors(error.fieldErrors());
        const mapped = ["delivery_point", "delivery_address", "bonus_points"];
        if (error.details.every((d) => !mapped.includes(d.field))) setFormError(error.message);
      } else {
        setFormError(error.message);
      }
      // A changed balance or menu means the quote is stale too.
      void summary.mutate();
      setSubmitting(false);
    }
  }

  if (!hydrated) {
    return <CheckoutSkeleton />;
  }

  if (leaving) {
    return (
      <main className="mx-auto w-full max-w-xl flex-1 px-4 py-24 text-center" aria-busy>
        <p className="font-serif text-3xl text-ink">
          {leaving === "payment" ? "Taking you to payment…" : "Order placed"}
        </p>
        <p className="mt-3 text-muted-ink">Don&apos;t close this page.</p>
      </main>
    );
  }

  if (!cart.restaurant || cart.items.length === 0) {
    return (
      <main className="mx-auto w-full max-w-xl flex-1 px-4 py-20 text-center">
        <h1 className="font-serif text-4xl text-ink">Nothing to check out</h1>
        <p className="mt-3 text-muted-ink">Your cart is empty. Add a few dishes first.</p>
        <Link
          href="/"
          className="mt-6 inline-block rounded-full bg-accent px-5 py-2.5 text-sm font-semibold text-white hover:bg-accent-strong"
        >
          Browse restaurants
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-4 pb-16 pt-6 sm:px-6 lg:px-8">
      <Link href="/cart" className="inline-flex items-center gap-1.5 text-sm text-muted-ink hover:text-ink">
        <ArrowLeft aria-hidden className="h-4 w-4" />
        Back to cart
      </Link>
      <h1 className="mt-4 font-serif text-4xl tracking-tight text-ink">Checkout</h1>

      <div className="mt-8 grid gap-10 lg:grid-cols-[1fr_22rem]">
        <div className="space-y-8">
          <Section step={1} title="How should it reach you?">
            <MethodSelector
              value={method}
              onChange={(next) => {
                setMethod(next);
                setSubmitErrors({});
              }}
              quotes={methodQuotes}
            />
          </Section>

          <Section step={2} title={isPickup ? "Where to pick it up" : "Where to deliver"}>
            {isPickup ? (
              <p className="inline-flex items-start gap-2 text-ink">
                <MapPin aria-hidden className="mt-0.5 h-4 w-4 shrink-0 text-sage" />
                <span>
                  {cart.restaurant.name}
                  {restaurant && <span className="block text-sm text-muted-ink">{restaurant.address}</span>}
                </span>
              </p>
            ) : (
              <>
                <p className="mb-3 text-sm text-muted-ink">
                  Click the map where the courier should bring the order
                  {quote ? ` (within ${quote.delivery_radius_km} km of the restaurant)` : ""}.
                </p>
                <div
                  className={`h-80 overflow-hidden rounded-xl border ${
                    fieldError("delivery_point") ? "border-accent-strong" : "border-line"
                  }`}
                >
                  {restaurant ? (
                    <DeliveryMap
                      restaurant={{ lat: restaurant.lat, lng: restaurant.lng, name: restaurant.name }}
                      point={point}
                      radiusKm={quote?.delivery_radius_km ?? null}
                      onPick={(picked) => {
                        setPoint(picked);
                        setSubmitErrors((errors) => withoutKey(errors, "delivery_point"));
                      }}
                    />
                  ) : (
                    <div className="h-full w-full animate-pulse bg-surface" />
                  )}
                </div>
                <FieldError message={fieldError("delivery_point")} />
                {point && quote?.delivery.distance_km != null && !fieldError("delivery_point") && (
                  <p className="mt-2 text-sm text-muted-ink">About {quote.delivery.distance_km.toFixed(1)} km by road.</p>
                )}
                <div className="mt-5 grid gap-4 sm:grid-cols-2">
                  <FormField
                    label="Street and building"
                    placeholder="vul. Kniazia Romana 12"
                    autoComplete="street-address"
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    error={fieldError("delivery_address")}
                  />
                  <FormField
                    label="Apartment, entrance, notes"
                    placeholder="apt 7, ring twice"
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    hint="Optional"
                  />
                </div>
              </>
            )}
          </Section>

          {quote && quote.loyalty.points_balance > 0 && (
            <Section step={3} title="Bonus points">
              <p className="text-sm text-muted-ink">
                You have {pluralize(quote.loyalty.points_balance, "point", "points")}. On this order you can use up
                to {maxPoints}; one point is worth 1 ₴.
              </p>
              <div className="mt-4 flex items-center gap-4">
                <input
                  type="range"
                  min={0}
                  max={maxPoints}
                  value={Math.min(points, maxPoints)}
                  onChange={(e) => setPoints(Number(e.target.value))}
                  disabled={maxPoints === 0}
                  aria-label="Points to use"
                  className="flex-1 accent-[var(--accent)]"
                />
                <span className="w-24 text-right text-sm font-medium tabular-nums text-ink">
                  {points} pts
                </span>
                <button
                  type="button"
                  onClick={() => setPoints(points === maxPoints ? 0 : maxPoints)}
                  disabled={maxPoints === 0}
                  className="rounded-full border border-line px-3 py-1 text-sm text-ink hover:bg-surface disabled:opacity-40"
                >
                  {points === maxPoints && maxPoints > 0 ? "None" : "Max"}
                </button>
              </div>
              <FieldError message={fieldError("bonus_points")} />
            </Section>
          )}

          <Section step={quote && quote.loyalty.points_balance > 0 ? 4 : 3} title="Payment">
            <div role="radiogroup" aria-label="Payment method" className="grid gap-3 sm:grid-cols-2">
              {(
                [
                  { value: "stripe", icon: CreditCard, title: "Card online", note: "Visa or Mastercard via Stripe" },
                  {
                    value: "cash",
                    icon: Banknote,
                    title: isPickup ? "Pay at pickup" : "Cash to the courier",
                    note: "Pay when you get the order",
                  },
                ] as const
              ).map((option) => (
                <button
                  key={option.value}
                  type="button"
                  role="radio"
                  aria-checked={payment === option.value}
                  onClick={() => setPayment(option.value)}
                  className={`flex items-start gap-3 rounded-xl border p-4 text-left transition ${
                    payment === option.value
                      ? "border-ink bg-card ring-1 ring-ink"
                      : "border-line bg-card hover:border-muted-ink/50"
                  }`}
                >
                  <option.icon aria-hidden className="mt-0.5 h-4 w-4 text-sage" />
                  <span>
                    <span className="block font-medium text-ink">{option.title}</span>
                    <span className="block text-xs text-muted-ink">{option.note}</span>
                  </span>
                </button>
              ))}
            </div>
          </Section>
        </div>

        <aside className="h-fit rounded-xl bg-surface p-5 lg:sticky lg:top-6" aria-busy={summary.isValidating}>
          {quote ? (
            <div className={summary.isValidating ? "opacity-70 transition-opacity" : ""}>
              <OrderSummary quote={quote} restaurantName={cart.restaurant.name} />
            </div>
          ) : summary.error ? (
            <p role="alert" className="text-sm text-accent-strong">
              {summary.error.message}
            </p>
          ) : (
            <SummarySkeleton />
          )}

          {(generalIssue || formError) && (
            <div role="alert" className="mt-4 rounded-lg border border-accent-strong/30 bg-accent/10 px-3 py-2.5 text-sm text-accent-strong">
              {formError ?? generalIssue?.message}
              {generalIssue?.field === "items" && (
                <Link href="/cart" className="mt-1 block font-medium underline underline-offset-2">
                  Edit the cart
                </Link>
              )}
            </div>
          )}

          <button
            type="button"
            onClick={() => void placeOrder()}
            disabled={!canSubmit}
            className="mt-5 w-full rounded-full bg-accent px-5 py-3 font-semibold text-white transition hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting ? "Placing order…" : quote ? `Place order · ${formatPrice(quote.total)}` : "Place order"}
          </button>
          {issue?.field === "delivery_point" && (
            <p className="mt-2 text-center text-xs text-muted-ink">{issue.message}</p>
          )}
        </aside>
      </div>
    </main>
  );
}

function SummarySkeleton() {
  return (
    <div aria-hidden className="space-y-3">
      <div className="h-4 w-24 animate-pulse rounded bg-background" />
      <div className="h-6 w-40 animate-pulse rounded bg-background" />
      <div className="h-24 animate-pulse rounded bg-background" />
      <div className="h-8 animate-pulse rounded bg-background" />
    </div>
  );
}

function CheckoutSkeleton() {
  return (
    <main className="mx-auto w-full max-w-6xl flex-1 space-y-4 px-4 pt-10 sm:px-6 lg:px-8" aria-busy>
      <div className="h-10 w-48 animate-pulse rounded-lg bg-surface" />
      <div className="grid gap-10 lg:grid-cols-[1fr_22rem]">
        <div className="h-96 animate-pulse rounded-xl bg-surface" />
        <div className="h-72 animate-pulse rounded-xl bg-surface" />
      </div>
    </main>
  );
}
