"use client";

import { useState } from "react";
import useSWR from "swr";

import { FormField } from "@/components/form-field";
import { api } from "@/lib/api";
import { inputToKopiyky, kopiykyToInput } from "@/lib/format";
import { useAsyncAction } from "@/lib/use-async-action";
import type { LoyaltySettings } from "@/types/admin";

type Draft = Record<keyof LoyaltySettings, string>;
const MONEY_FIELDS: (keyof LoyaltySettings)[] = ["point_value", "premium_card_price"];

function toDraft(settings: LoyaltySettings): Draft {
  return Object.fromEntries(
    Object.entries(settings).map(([key, value]) => [
      key,
      MONEY_FIELDS.includes(key as keyof LoyaltySettings) ? kopiykyToInput(value) : String(value),
    ]),
  ) as Draft;
}

function SettingsForm({ settings, onSaved }: { settings: LoyaltySettings; onSaved: (s: LoyaltySettings) => void }) {
  const [draft, setDraft] = useState<Draft>(() => toDraft(settings));
  const [saved, setSaved] = useState(false);
  const [moneyErrors, setMoneyErrors] = useState<Record<string, string>>({});
  const action = useAsyncAction();
  const set = (field: keyof LoyaltySettings) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setDraft({ ...draft, [field]: e.target.value });
    setSaved(false);
  };
  const errorFor = (field: keyof LoyaltySettings) => moneyErrors[field] ?? action.fieldErrors[field];

  async function submit() {
    const errors: Record<string, string> = {};
    const payload = Object.fromEntries(
      Object.entries(draft).map(([key, value]) => {
        if (MONEY_FIELDS.includes(key as keyof LoyaltySettings)) {
          const kopiyky = inputToKopiyky(value);
          if (kopiyky === null) errors[key] = "Enter an amount like 99 or 1.50.";
          return [key, kopiyky ?? 0];
        }
        return [key, Number(value)];
      }),
    ) as unknown as LoyaltySettings;
    setMoneyErrors(errors);
    if (Object.keys(errors).length > 0) return;
    const result = await action.run(() => api.put<LoyaltySettings>("/admin/loyalty-settings", payload));
    if (result) {
      onSaved(result);
      setSaved(true);
    }
  }

  return (
    <form
      noValidate
      className="space-y-8"
      onSubmit={(event) => {
        event.preventDefault();
        void submit();
      }}
    >
      <fieldset className="grid gap-4 sm:grid-cols-3">
        <legend className="mb-3 font-serif text-xl text-ink">Bonus points</legend>
        <FormField label="Points per 100 ₴" type="number" min={0} value={draft.points_per_100_uah} onChange={set("points_per_100_uah")} error={errorFor("points_per_100_uah")} />
        <FormField label="Value of 1 point, ₴" inputMode="decimal" value={draft.point_value} onChange={set("point_value")} error={errorFor("point_value")} />
        <FormField label="Max share paid with points, %" type="number" min={0} max={100} value={draft.max_points_redemption_percent} onChange={set("max_points_redemption_percent")} error={errorFor("max_points_redemption_percent")} />
      </fieldset>
      <fieldset className="grid gap-4 sm:grid-cols-3">
        <legend className="mb-3 font-serif text-xl text-ink">Regular customers</legend>
        <FormField label="Delivered orders to qualify" type="number" min={1} value={draft.regular_customer_threshold} onChange={set("regular_customer_threshold")} error={errorFor("regular_customer_threshold")} />
        <FormField label="Discount, %" type="number" min={0} max={50} value={draft.regular_customer_discount_percent} onChange={set("regular_customer_discount_percent")} error={errorFor("regular_customer_discount_percent")} />
      </fieldset>
      <fieldset className="grid gap-4 sm:grid-cols-3">
        <legend className="mb-3 font-serif text-xl text-ink">Premium card</legend>
        <FormField label="Price, ₴" inputMode="decimal" value={draft.premium_card_price} onChange={set("premium_card_price")} error={errorFor("premium_card_price")} />
        <FormField label="Valid for, days" type="number" min={1} value={draft.premium_card_days} onChange={set("premium_card_days")} error={errorFor("premium_card_days")} />
      </fieldset>
      <div className="flex items-center gap-4 border-t border-line pt-5">
        <button type="submit" disabled={action.pending} className="rounded-full bg-accent px-5 py-2.5 text-sm font-semibold text-white hover:bg-accent-strong disabled:opacity-50">
          {action.pending ? "Saving…" : "Save settings"}
        </button>
        {saved && (
          <span role="status" className="text-sm text-sage">
            Saved. New orders use these values.
          </span>
        )}
      </div>
    </form>
  );
}

export function LoyaltySettingsForm() {
  const { data, mutate } = useSWR<LoyaltySettings>("/admin/loyalty-settings");
  return (
    <div className="max-w-3xl">
      <h1 className="font-serif text-3xl text-ink">Loyalty</h1>
      <p className="mt-1 text-sm text-muted-ink">
        Changes apply to the next quote, delivery and premium purchase. Points already earned stay as they are.
      </p>
      <div className="mt-6">
        {data ? (
          <SettingsForm settings={data} onSaved={(s) => void mutate(s, { revalidate: false })} />
        ) : (
          <div className="h-80 animate-pulse rounded-xl bg-surface" aria-busy />
        )}
      </div>
    </div>
  );
}
