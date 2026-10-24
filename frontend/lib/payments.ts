"use client";

import { useState } from "react";

import { ApiError, api } from "./api";

/** Starts a new payment attempt for an unpaid order and sends the browser to pay. */
export function usePayAgain(orderId: number) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function payAgain() {
    setPending(true);
    setError(null);
    try {
      const { redirect_url } = await api.post<{ redirect_url: string }>(`/orders/${orderId}/payment-session`);
      // Stripe Checkout is another site, so this is a full navigation, not a router push.
      window.location.assign(redirect_url);
    } catch (err) {
      if (!(err instanceof ApiError)) throw err;
      setError(err.message);
      setPending(false);
    }
  }

  return { payAgain, pending, error };
}
