"use client";

import { Minus, Plus } from "lucide-react";

import { MAX_ITEM_QUANTITY } from "@/lib/cart-store";

export function QuantityStepper({
  quantity,
  onChange,
  label,
  size = "md",
}: {
  quantity: number;
  onChange: (quantity: number) => void;
  /** Dish name, for screen-reader labels. */
  label: string;
  size?: "sm" | "md";
}) {
  const button = size === "sm" ? "h-7 w-7" : "h-8 w-8";
  return (
    <div className="inline-flex items-center rounded-full border border-line bg-card">
      <button
        type="button"
        onClick={() => onChange(quantity - 1)}
        aria-label={quantity === 1 ? `Remove ${label}` : `One less ${label}`}
        className={`${button} flex items-center justify-center rounded-full text-ink hover:bg-surface`}
      >
        <Minus aria-hidden className="h-3.5 w-3.5" />
      </button>
      <span className="min-w-6 text-center text-sm font-medium tabular-nums text-ink" aria-live="polite">
        {quantity}
      </span>
      <button
        type="button"
        onClick={() => onChange(quantity + 1)}
        disabled={quantity >= MAX_ITEM_QUANTITY}
        aria-label={`One more ${label}`}
        className={`${button} flex items-center justify-center rounded-full text-ink hover:bg-surface disabled:opacity-40`}
      >
        <Plus aria-hidden className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}
