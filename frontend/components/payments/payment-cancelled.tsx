"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { usePayAgain } from "@/lib/payments";

/** Return page when the customer backs out of the payment form. The order is kept. */
export function PaymentCancelled() {
  const orderId = Number(useSearchParams().get("order_id"));
  const valid = Number.isInteger(orderId) && orderId > 0;
  const { payAgain, pending, error } = usePayAgain(orderId);

  return (
    <main className="mx-auto w-full max-w-xl flex-1 px-4 py-20 text-center">
      <h1 className="font-serif text-4xl text-ink">Payment cancelled</h1>
      <p className="mt-3 text-muted-ink">
        {valid
          ? `Order #${orderId} is saved and waits for payment. Nothing was charged.`
          : "Nothing was charged."}
      </p>
      {error && (
        <p role="alert" className="mt-4 text-sm text-accent-strong">
          {error}
        </p>
      )}
      {valid && (
        <div className="mt-6 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <button
            type="button"
            onClick={() => void payAgain()}
            disabled={pending}
            className="rounded-full bg-accent px-6 py-3 font-semibold text-white hover:bg-accent-strong disabled:opacity-50"
          >
            {pending ? "Opening payment…" : "Try paying again"}
          </button>
          <Link
            href={`/orders/${orderId}`}
            className="rounded-full border border-ink px-6 py-3 font-semibold text-ink hover:bg-ink hover:text-background"
          >
            View order
          </Link>
        </div>
      )}
    </main>
  );
}
