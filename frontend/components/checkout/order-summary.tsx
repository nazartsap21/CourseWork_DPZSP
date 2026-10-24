import { formatDeliveryWindow, formatPrice } from "@/lib/format";
import type { Quote } from "@/types/orders";

function formatAmount(line: { code: string; amount: number }): string {
  if (line.code === "delivery" && line.amount === 0) return "Free";
  return line.amount < 0 ? `−${formatPrice(-line.amount)}` : formatPrice(line.amount);
}

/** Price breakdown as returned by the quote: one row per price component. */
export function OrderSummary({ quote, restaurantName }: { quote: Quote; restaurantName: string }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-sage">Your order</p>
      <p className="mt-1 font-serif text-xl text-ink">{restaurantName}</p>

      <ul className="mt-4 space-y-1.5 text-sm">
        {quote.items.map((item) => (
          <li key={item.dish_id} className="flex justify-between gap-3">
            <span className="text-ink">
              <span className="tabular-nums text-muted-ink">{item.quantity} × </span>
              {item.name}
            </span>
            <span className="tabular-nums text-ink">{formatPrice(item.line_total)}</span>
          </li>
        ))}
      </ul>

      <dl className="mt-4 space-y-1.5 border-t border-line pt-4 text-sm">
        {quote.lines.map((line) => (
          <div key={line.code} className="flex justify-between gap-3">
            <dt className="text-muted-ink">{line.label}</dt>
            <dd className={`tabular-nums ${line.amount < 0 ? "text-sage" : "text-ink"}`}>{formatAmount(line)}</dd>
          </div>
        ))}
      </dl>

      <div className="mt-4 flex items-baseline justify-between border-t border-line pt-4">
        <span className="font-medium text-ink">Total</span>
        <span className="font-serif text-2xl tabular-nums text-ink">{formatPrice(quote.total)}</span>
      </div>
      <p className="mt-1 text-right text-xs text-muted-ink">
        {quote.delivery.needs_courier ? "Delivery in " : "Ready in "}
        {formatDeliveryWindow(quote.delivery.eta_minutes_min, quote.delivery.eta_minutes_max)}
      </p>
    </div>
  );
}
