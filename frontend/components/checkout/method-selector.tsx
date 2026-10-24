"use client";

import { Bike, Store, Zap } from "lucide-react";

import { formatDeliveryWindow, formatPrice } from "@/lib/format";
import { DELIVERY_METHOD_LABELS } from "@/lib/order-labels";
import type { DeliveryMethod, Quote } from "@/types/orders";

const ICONS = { standard: Bike, express: Zap, pickup: Store } satisfies Record<DeliveryMethod, unknown>;
export const DELIVERY_METHODS: DeliveryMethod[] = ["standard", "express", "pickup"];

export function MethodSelector({
  value,
  onChange,
  quotes,
}: {
  value: DeliveryMethod;
  onChange: (method: DeliveryMethod) => void;
  /** Quote per method (without points), for the fee and time on each option. */
  quotes: Partial<Record<DeliveryMethod, Quote>>;
}) {
  return (
    <div role="radiogroup" aria-label="Delivery method" className="grid gap-3 sm:grid-cols-3">
      {DELIVERY_METHODS.map((method) => {
        const Icon = ICONS[method];
        const quote = quotes[method];
        const selected = value === method;
        return (
          <button
            key={method}
            type="button"
            role="radio"
            aria-checked={selected}
            onClick={() => onChange(method)}
            className={`rounded-xl border p-4 text-left transition ${
              selected ? "border-ink bg-card ring-1 ring-ink" : "border-line bg-card hover:border-muted-ink/50"
            }`}
          >
            <span className="flex items-center justify-between">
              <span className="inline-flex items-center gap-2 font-medium text-ink">
                <Icon aria-hidden className="h-4 w-4 text-sage" />
                {DELIVERY_METHOD_LABELS[method].title}
              </span>
              <span className="text-sm font-medium tabular-nums text-ink">
                {quote ? (quote.delivery.fee === 0 ? "Free" : formatPrice(quote.delivery.fee)) : "…"}
              </span>
            </span>
            <span className="mt-1 block text-xs text-muted-ink">{DELIVERY_METHOD_LABELS[method].description}</span>
            <span className="mt-2 block text-sm text-ink">
              {quote
                ? formatDeliveryWindow(quote.delivery.eta_minutes_min, quote.delivery.eta_minutes_max)
                : " "}
            </span>
          </button>
        );
      })}
    </div>
  );
}
