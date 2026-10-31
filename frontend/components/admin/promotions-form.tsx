"use client";

import { useState } from "react";

import { api } from "@/lib/api";
import { pluralize } from "@/lib/format";
import { useAsyncAction } from "@/lib/use-async-action";

const MAX_LENGTH = 500;

/** Sends one in-app notification to every customer (shown in their bell). */
export function PromotionsForm() {
  const [message, setMessage] = useState("");
  const [confirming, setConfirming] = useState(false);
  const [sentTo, setSentTo] = useState<number | null>(null);
  const action = useAsyncAction();

  async function send() {
    const result = await action.run(() => api.post<{ recipients: number }>("/admin/promotions", { message }));
    setConfirming(false);
    if (result) {
      setSentTo(result.recipients);
      setMessage("");
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="font-serif text-3xl text-ink">Promotions</h1>
      <p className="mt-1 text-sm text-muted-ink">
        A short message for every customer, shown in their notifications: new restaurants, weekend deals.
      </p>

      <label htmlFor="promo-message" className="mt-6 block text-sm font-medium text-ink">
        Message
      </label>
      <textarea
        id="promo-message"
        rows={4}
        value={message}
        onChange={(e) => {
          setMessage(e.target.value.slice(0, MAX_LENGTH));
          setSentTo(null);
        }}
        placeholder="Supra Courtyard now delivers on Sundays. Khachapuri is 15% off this weekend."
        className="mt-1.5 w-full rounded-lg border border-line bg-card px-3 py-2.5 text-ink outline-none focus:border-accent focus:ring-2 focus:ring-accent/30"
      />
      <p className="mt-1 text-right text-xs text-muted-ink">
        {message.length}/{MAX_LENGTH}
      </p>
      {(action.fieldErrors.message || action.error) && (
        <p role="alert" className="text-sm text-accent-strong">
          {action.fieldErrors.message ?? action.error}
        </p>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-3">
        {confirming ? (
          <span className="inline-flex items-center gap-2 rounded-full bg-surface py-1 pl-4 pr-1 text-sm">
            Send to all customers?
            <button type="button" onClick={() => void send()} disabled={action.pending} className="rounded-full bg-accent px-3 py-1.5 font-semibold text-white disabled:opacity-50">
              {action.pending ? "Sending…" : "Send"}
            </button>
            <button type="button" onClick={() => setConfirming(false)} className="rounded-full px-3 py-1.5 hover:bg-background">
              Not yet
            </button>
          </span>
        ) : (
          <button
            type="button"
            disabled={message.trim().length < 5}
            onClick={() => setConfirming(true)}
            className="rounded-full bg-accent px-5 py-2.5 text-sm font-semibold text-white hover:bg-accent-strong disabled:opacity-50"
          >
            Send promotion
          </button>
        )}
        {sentTo !== null && (
          <span role="status" className="text-sm text-sage">
            Sent to {pluralize(sentTo, "customer", "customers")}.
          </span>
        )}
      </div>
    </div>
  );
}
