"use client";

import useSWR from "swr";

import type { Quote, QuotePayload } from "@/types/orders";

import { api, type ApiError } from "./api";

type QuoteKey = readonly [path: "/orders/quote", body: string];

const postQuote = ([path, body]: QuoteKey) => api.post<Quote>(path, JSON.parse(body));

/**
 * Live quote for a prospective order. The key carries the serialized payload,
 * so identical payloads share one request and every change refetches.
 * Pass `null` to skip fetching.
 */
export function useQuote(payload: QuotePayload | null) {
  const key: QuoteKey | null = payload ? ["/orders/quote", JSON.stringify(payload)] : null;
  return useSWR<Quote, ApiError, QuoteKey | null>(key, postQuote, {
    keepPreviousData: true,
    revalidateOnFocus: false,
  });
}
