"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import type { ReorderResult } from "@/types/orders";

import { ApiError, api } from "./api";
import { useCart } from "./cart";
import { formatPrice } from "./format";

const NOTICE_KEY = "forkful.reorder-notice";

export interface ReorderNotice {
  orderId: number;
  restaurantName: string;
  lines: string[];
}

function noticeLines(result: ReorderResult): string[] {
  return [
    ...result.skipped.map((item) => `${item.name} is ${item.reason}.`),
    ...result.price_changes.map(
      (change) => `${change.name} now costs ${formatPrice(change.new_price)} (was ${formatPrice(change.old_price)}).`,
    ),
  ];
}

/** One-click reorder: the server rebuilds the cart from today's menu, we put it in the cart and open it. */
export function useReorder() {
  const router = useRouter();
  const { replace } = useCart();
  const [pendingId, setPendingId] = useState<number | null>(null);
  const [error, setError] = useState<{ orderId: number; message: string } | null>(null);

  async function reorder(orderId: number) {
    setPendingId(orderId);
    setError(null);
    try {
      const result = await api.post<ReorderResult>(`/orders/${orderId}/reorder`);
      replace({
        restaurant: result.restaurant,
        items: result.items.map(({ dish_id, name, price, quantity }) => ({ dish_id, name, price, quantity })),
      });
      // The cart page shows what was skipped or repriced once, then forgets it.
      const notice: ReorderNotice = { orderId, restaurantName: result.restaurant.name, lines: noticeLines(result) };
      try {
        window.sessionStorage.setItem(NOTICE_KEY, JSON.stringify(notice));
      } catch {
        // Without storage the cart still works; only the notice is lost.
      }
      router.push("/cart");
    } catch (err) {
      if (!(err instanceof ApiError)) throw err;
      setError({ orderId, message: err.message });
      setPendingId(null);
    }
  }

  return { reorder, pendingId, errorFor: (orderId: number) => (error?.orderId === orderId ? error.message : null) };
}

/** The notice left by the last reorder, if any (read-only; see `clearReorderNotice`). */
export function readReorderNotice(): ReorderNotice | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.sessionStorage.getItem(NOTICE_KEY);
    return raw ? (JSON.parse(raw) as ReorderNotice) : null;
  } catch {
    return null;
  }
}

export function clearReorderNotice(): void {
  try {
    window.sessionStorage.removeItem(NOTICE_KEY);
  } catch {
    // Nothing to clear without storage.
  }
}
