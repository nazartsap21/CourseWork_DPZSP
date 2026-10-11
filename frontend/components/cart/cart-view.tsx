"use client";

import { ArrowLeft, Trash2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo } from "react";
import useSWR from "swr";

import type { ApiError } from "@/lib/api";
import { useCart } from "@/lib/cart";
import type { CartDish, CartItem } from "@/lib/cart-store";
import { formatPrice } from "@/lib/format";
import { useHydrated } from "@/lib/use-hydrated";
import type { Menu } from "@/types/catalog";

import { QuantityStepper } from "./quantity-stepper";

export function CartView() {
  const { cart, setQuantity, syncPrices, clear, canOrder } = useCart();
  const hydrated = useHydrated();
  const restaurant = cart.restaurant;

  // The cart stores snapshots; the live menu tells us about price changes and sold-out dishes.
  const { data: menu, error: menuError } = useSWR<Menu, ApiError>(
    restaurant ? `/restaurants/${restaurant.id}/menu` : null,
  );
  const available = useMemo(() => {
    const dishes = new Map<number, CartDish>();
    menu?.sections.forEach((section) =>
      section.dishes.filter((dish) => dish.is_available).forEach((dish) => dishes.set(dish.id, dish)),
    );
    return dishes;
  }, [menu]);

  useEffect(() => {
    if (menu) syncPrices(available);
  }, [menu, available, syncPrices]);

  const restaurantClosed = menuError?.status === 404;
  const isUnavailable = (item: CartItem) => restaurantClosed || (menu !== undefined && !available.has(item.dish_id));
  const unavailableCount = cart.items.filter(isUnavailable).length;
  const orderableSubtotal = cart.items
    .filter((item) => !isUnavailable(item))
    .reduce((sum, item) => sum + item.price * item.quantity, 0);
  const minimum = restaurant?.min_order_amount ?? 0;
  const missing = Math.max(minimum - orderableSubtotal, 0);
  const canCheckout = canOrder && !restaurantClosed && unavailableCount === 0 && missing === 0 && menu !== undefined;

  if (!hydrated) {
    return (
      <main className="mx-auto w-full max-w-6xl flex-1 space-y-4 px-4 pt-10 sm:px-6 lg:px-8" aria-busy>
        <div className="h-10 w-56 animate-pulse rounded-lg bg-surface" />
        <div className="h-48 animate-pulse rounded-xl bg-surface" />
      </main>
    );
  }

  if (!restaurant || cart.items.length === 0) {
    return (
      <main className="mx-auto w-full max-w-xl flex-1 px-4 py-20 text-center">
        <h1 className="font-serif text-4xl text-ink">Your cart is empty</h1>
        <p className="mt-3 text-muted-ink">Pick a restaurant and add a few dishes to start an order.</p>
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
      <Link
        href={`/restaurants/${restaurant.id}`}
        className="inline-flex items-center gap-1.5 text-sm text-muted-ink hover:text-ink"
      >
        <ArrowLeft aria-hidden className="h-4 w-4" />
        Back to {restaurant.name}
      </Link>
      <h1 className="mt-4 font-serif text-4xl tracking-tight text-ink">Your order</h1>
      <p className="mt-1 text-muted-ink">from {restaurant.name}</p>

      {restaurantClosed && (
        <p role="alert" className="mt-6 rounded-lg border border-accent-strong/30 bg-accent/10 px-4 py-3 text-sm text-accent-strong">
          {restaurant.name} isn&apos;t taking orders right now. Clear the cart to order from another restaurant.
        </p>
      )}
      {!restaurantClosed && unavailableCount > 0 && (
        <p role="alert" className="mt-6 rounded-lg border border-accent-strong/30 bg-accent/10 px-4 py-3 text-sm text-accent-strong">
          {unavailableCount === 1 ? "One dish is" : `${unavailableCount} dishes are`} no longer available. Remove{" "}
          {unavailableCount === 1 ? "it" : "them"} to continue.
        </p>
      )}

      <div className="mt-8 grid gap-10 lg:grid-cols-[1fr_22rem]">
        <ul className="border-t border-line">
          {cart.items.map((item) => {
            const unavailable = isUnavailable(item);
            return (
              <li key={item.dish_id} className="flex items-center gap-4 border-b border-line py-4">
                <div className="min-w-0 flex-1">
                  <p className={`font-medium ${unavailable ? "text-muted-ink line-through" : "text-ink"}`}>{item.name}</p>
                  <p className="mt-0.5 text-sm text-muted-ink">
                    {unavailable ? <span className="text-accent-strong">No longer available</span> : formatPrice(item.price)}
                  </p>
                </div>
                {unavailable ? (
                  <button
                    type="button"
                    onClick={() => setQuantity(item.dish_id, 0)}
                    className="inline-flex items-center gap-1.5 rounded-full border border-line px-3 py-1.5 text-sm text-ink hover:bg-surface"
                  >
                    <Trash2 aria-hidden className="h-4 w-4" />
                    Remove
                  </button>
                ) : (
                  <div className="flex flex-col items-end gap-2 sm:flex-row sm:items-center sm:gap-4">
                    <QuantityStepper
                      quantity={item.quantity}
                      label={item.name}
                      onChange={(quantity) => setQuantity(item.dish_id, quantity)}
                    />
                    <p className="w-20 text-right font-medium tabular-nums text-ink">
                      {formatPrice(item.price * item.quantity)}
                    </p>
                  </div>
                )}
              </li>
            );
          })}
        </ul>

        <aside className="h-fit rounded-xl bg-surface p-5 lg:sticky lg:top-6">
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-muted-ink">Subtotal</dt>
              <dd className="font-medium tabular-nums text-ink">{formatPrice(orderableSubtotal)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-ink">Delivery</dt>
              <dd className="text-muted-ink">at checkout</dd>
            </div>
          </dl>

          {minimum > 0 && (
            <div className="mt-4">
              <div
                className="h-1.5 overflow-hidden rounded-full bg-background"
                role="progressbar"
                aria-label="Minimum order"
                aria-valuemin={0}
                aria-valuemax={minimum}
                aria-valuenow={Math.min(orderableSubtotal, minimum)}
              >
                <div
                  className={`h-full rounded-full ${missing === 0 ? "bg-sage" : "bg-saffron"}`}
                  style={{ width: `${Math.min(orderableSubtotal / minimum, 1) * 100}%` }}
                />
              </div>
              <p className="mt-2 text-xs text-muted-ink">
                {missing > 0
                  ? `Add ${formatPrice(missing)} more to reach the ${formatPrice(minimum)} minimum.`
                  : `Minimum order of ${formatPrice(minimum)} reached.`}
              </p>
            </div>
          )}

          {canCheckout ? (
            <Link
              href="/checkout"
              className="mt-5 block rounded-full bg-accent px-5 py-3 text-center font-semibold text-white transition hover:bg-accent-strong"
            >
              Go to checkout
            </Link>
          ) : (
            <button
              type="button"
              disabled
              className="mt-5 w-full cursor-not-allowed rounded-full bg-accent px-5 py-3 font-semibold text-white opacity-50"
            >
              Go to checkout
            </button>
          )}
          <p className="mt-3 text-xs text-muted-ink">Delivery fee, discounts and bonus points are applied at checkout.</p>

          <button
            type="button"
            onClick={clear}
            className="mt-5 inline-flex items-center gap-1.5 text-sm text-muted-ink hover:text-accent-strong"
          >
            <Trash2 aria-hidden className="h-4 w-4" />
            Clear cart
          </button>
        </aside>
      </div>
    </main>
  );
}
