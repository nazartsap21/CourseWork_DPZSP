"use client";

import { ShoppingBag } from "lucide-react";
import Link from "next/link";

import { useCart } from "@/lib/cart";
import { formatPrice, pluralize } from "@/lib/format";

/** Bottom bar on a restaurant page while the cart holds this restaurant's dishes. */
export function OrderBar({ restaurantId }: { restaurantId: number }) {
  const { cart, itemCount, subtotal, canOrder } = useCart();
  if (!canOrder || cart.restaurant?.id !== restaurantId || itemCount === 0) return null;

  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-0 z-20 px-4 pb-4 sm:pb-6">
      <Link
        href="/cart"
        className="pointer-events-auto mx-auto flex max-w-md items-center justify-between gap-4 rounded-full bg-ink px-5 py-3 text-background shadow-[0_12px_32px_rgba(34,25,22,0.25)] transition hover:bg-accent-strong"
      >
        <span className="inline-flex items-center gap-2 text-sm">
          <ShoppingBag aria-hidden className="h-4 w-4" />
          {pluralize(itemCount, "item", "items")}
        </span>
        <span className="font-semibold">View order · {formatPrice(subtotal)}</span>
      </Link>
    </div>
  );
}
