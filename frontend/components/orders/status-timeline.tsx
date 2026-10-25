import { Check, X } from "lucide-react";

import type { Order, OrderStatus } from "@/types/orders";

const timeFormat = new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit" });

interface Step {
  status: OrderStatus;
  label: string;
}

/** The path an order of this kind goes through; pickup orders skip the courier. */
function stepsFor(order: Order): Step[] {
  const paysOnline = order.payment_method !== "cash";
  const steps: Step[] = [
    ...(paysOnline ? [{ status: "pending_payment" as const, label: "Order placed" }] : []),
    { status: "accepted", label: paysOnline ? "Paid and accepted" : "Accepted" },
    { status: "preparing", label: "Preparing" },
  ];
  if (order.delivery_method === "pickup") {
    steps.push({ status: "ready_for_pickup", label: "Ready for pickup" }, { status: "delivered", label: "Collected" });
  } else {
    steps.push(
      { status: "ready_for_pickup", label: "Ready, waiting for a courier" },
      { status: "delivering", label: "On the way" },
      { status: "delivered", label: "Delivered" },
    );
  }
  return steps;
}

/**
 * Status timeline built from the order's history: reached steps show their
 * time, the current one is highlighted, the rest are what's still ahead.
 */
export function StatusTimeline({ order }: { order: Order }) {
  const reachedAt = new Map(order.status_history.map((entry) => [entry.status, entry.changed_at]));
  const steps = stepsFor(order);
  const cancelled = order.status === "cancelled";
  const currentIndex = steps.findIndex((step) => step.status === order.status);
  // For a cancelled order, the last step it actually reached.
  const lastReached = cancelled ? Math.max(...steps.map((s, i) => (reachedAt.has(s.status) ? i : -1))) : currentIndex;

  const visible = cancelled ? steps.slice(0, lastReached + 1) : steps;

  return (
    <ol className="relative space-y-0">
      {visible.map((step, index) => {
        const at = reachedAt.get(step.status);
        const done = index < lastReached || (index === lastReached && (order.status === "delivered" || cancelled));
        const current = !cancelled && index === currentIndex && order.status !== "delivered";
        const isLast = index === visible.length - 1 && !cancelled;
        return (
          <li key={step.status} className="relative flex gap-4 pb-6 last:pb-0">
            {!isLast && (
              <span
                aria-hidden
                className={`absolute left-[0.6875rem] top-6 h-full w-px ${index < lastReached || cancelled ? "bg-sage" : "bg-line"}`}
              />
            )}
            <span
              aria-hidden
              className={`relative z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 ${
                done
                  ? "border-sage bg-sage text-white"
                  : current
                    ? "border-accent bg-card"
                    : "border-line bg-card"
              }`}
            >
              {done && <Check className="h-3.5 w-3.5" strokeWidth={3} />}
              {current && <span className="h-2 w-2 animate-pulse rounded-full bg-accent" />}
            </span>
            <span className="flex min-w-0 flex-1 items-baseline justify-between gap-3">
              <span className={current ? "font-medium text-ink" : done ? "text-ink" : "text-muted-ink"}>
                {step.label}
                {current && <span className="sr-only"> (current)</span>}
              </span>
              {at && <span className="shrink-0 text-xs tabular-nums text-muted-ink">{timeFormat.format(new Date(at))}</span>}
            </span>
          </li>
        );
      })}
      {cancelled && (
        <li className="relative flex gap-4">
          <span
            aria-hidden
            className="relative z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 border-accent-strong bg-accent-strong text-white"
          >
            <X className="h-3.5 w-3.5" strokeWidth={3} />
          </span>
          <span className="flex flex-1 items-baseline justify-between gap-3">
            <span className="font-medium text-accent-strong">Cancelled</span>
            {reachedAt.get("cancelled") && (
              <span className="text-xs tabular-nums text-muted-ink">
                {timeFormat.format(new Date(reachedAt.get("cancelled") as string))}
              </span>
            )}
          </span>
        </li>
      )}
    </ol>
  );
}
