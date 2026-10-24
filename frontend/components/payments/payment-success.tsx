"use client";

import { CheckCircle2 } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import useSWR from "swr";

import { ApiError, api } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import type { Order } from "@/types/orders";

type ConfirmKey = readonly [path: "/payments/confirm", sessionId: string];

const confirmPayment = ([path, sessionId]: ConfirmKey) => api.post<Order>(path, { session_id: sessionId });

/**
 * Return page after paying. The redirect alone proves nothing, so the backend
 * checks the session with the provider before the order moves on. Confirming
 * is idempotent, so a reload is harmless.
 */
export function PaymentSuccess() {
  const sessionId = useSearchParams().get("session_id");
  const { data: order, error } = useSWR<Order, ApiError, ConfirmKey | null>(
    sessionId ? ["/payments/confirm", sessionId] : null,
    confirmPayment,
    { revalidateOnFocus: false, revalidateIfStale: false, shouldRetryOnError: false },
  );

  if (!sessionId || error) {
    return (
      <main className="mx-auto w-full max-w-xl flex-1 px-4 py-20 text-center">
        <h1 className="font-serif text-4xl text-ink">We couldn&apos;t confirm the payment</h1>
        <p className="mt-3 text-muted-ink">
          {error?.message ?? "The payment link is incomplete."} If money was taken, it will show up on the order
          shortly.
        </p>
        <Link
          href="/"
          className="mt-6 inline-block rounded-full border border-ink px-5 py-2.5 text-sm font-semibold text-ink hover:bg-ink hover:text-background"
        >
          Back to restaurants
        </Link>
      </main>
    );
  }

  if (!order) {
    return (
      <main className="mx-auto w-full max-w-xl flex-1 px-4 py-24 text-center" aria-busy>
        <p className="font-serif text-3xl text-ink">Checking your payment…</p>
        <p className="mt-3 text-muted-ink">This takes a few seconds.</p>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-xl flex-1 px-4 py-20 text-center">
      <CheckCircle2 aria-hidden className="mx-auto h-10 w-10 text-sage" />
      <h1 className="mt-4 font-serif text-4xl text-ink">Payment received</h1>
      <p className="mt-3 text-muted-ink">
        {formatPrice(order.total)} paid for order #{order.id} from {order.restaurant.name}. The kitchen has your
        order.
      </p>
      <Link
        href={`/orders/${order.id}`}
        className="mt-6 inline-block rounded-full bg-accent px-6 py-3 font-semibold text-white hover:bg-accent-strong"
      >
        Track your order
      </Link>
    </main>
  );
}
