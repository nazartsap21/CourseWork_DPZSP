"use client";

import Link from "next/link";
import { useState } from "react";
import useSWR from "swr";

import { FormField } from "@/components/form-field";
import { api } from "@/lib/api";
import { useAsyncAction } from "@/lib/use-async-action";
import type { AdminCourier } from "@/types/admin";

function NewCourierForm({ onCreated }: { onCreated: () => Promise<unknown> }) {
  const [form, setForm] = useState({ name: "", email: "", phone: "", password: "" });
  const action = useAsyncAction();
  const set = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [field]: e.target.value });

  return (
    <form
      noValidate
      className="grid gap-4 rounded-xl border border-line bg-card p-4 sm:grid-cols-2"
      onSubmit={(event) => {
        event.preventDefault();
        void action.run(() => api.post("/admin/couriers", { ...form, phone: form.phone || null })).then(async (created) => {
          if (created) {
            setForm({ name: "", email: "", phone: "", password: "" });
            await onCreated();
          }
        });
      }}
    >
      <FormField label="Name" value={form.name} onChange={set("name")} error={action.fieldErrors.name} />
      <FormField label="Email" type="email" value={form.email} onChange={set("email")} error={action.fieldErrors.email} />
      <FormField label="Phone" type="tel" placeholder="+380" value={form.phone} onChange={set("phone")} error={action.fieldErrors.phone} />
      <FormField label="Temporary password" type="password" value={form.password} onChange={set("password")} error={action.fieldErrors.password} hint="At least 8 characters; the courier can change it in the account." />
      <div className="sm:col-span-2">
        <button type="submit" disabled={action.pending} className="rounded-full bg-accent px-4 py-2 text-sm font-semibold text-white hover:bg-accent-strong disabled:opacity-50">
          {action.pending ? "Creating…" : "Create courier account"}
        </button>
      </div>
    </form>
  );
}

export function CouriersManager() {
  const { data, mutate } = useSWR<{ items: AdminCourier[] }>("/admin/couriers", { refreshInterval: 15_000 });
  const [adding, setAdding] = useState(false);

  return (
    <div className="max-w-4xl">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="font-serif text-3xl text-ink">Couriers</h1>
        <button type="button" onClick={() => setAdding(!adding)} className="rounded-full border border-ink px-4 py-2 text-sm font-semibold text-ink hover:bg-ink hover:text-background">
          {adding ? "Close" : "New courier"}
        </button>
      </div>
      {adding && (
        <div className="mt-4">
          <NewCourierForm
            onCreated={async () => {
              setAdding(false);
              await mutate();
            }}
          />
        </div>
      )}

      {!data ? (
        <div className="mt-6 h-40 animate-pulse rounded-xl bg-surface" aria-busy />
      ) : data.items.length === 0 ? (
        <p className="mt-6 text-sm text-muted-ink">No couriers yet. Create the first account above.</p>
      ) : (
        <div className="mt-5 overflow-x-auto rounded-xl border border-line">
          <table className="w-full min-w-[36rem] text-left text-sm">
            <thead className="bg-surface text-xs uppercase tracking-wider text-muted-ink">
              <tr>
                <th className="px-4 py-2.5 font-medium">Courier</th>
                <th className="px-4 py-2.5 font-medium">Phone</th>
                <th className="px-4 py-2.5 font-medium">Active orders</th>
                <th className="px-4 py-2.5 text-right font-medium">Delivered today</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line bg-card">
              {data.items.map((courier) => (
                <tr key={courier.id}>
                  <td className="px-4 py-2.5">
                    <span className="font-medium text-ink">{courier.name}</span>
                    <span className="block text-xs text-muted-ink">{courier.email}</span>
                  </td>
                  <td className="px-4 py-2.5 text-muted-ink">{courier.phone ?? "—"}</td>
                  <td className="px-4 py-2.5">
                    {courier.active_order_ids.length === 0 ? (
                      <span className="text-muted-ink">Free</span>
                    ) : (
                      courier.active_order_ids.map((id) => (
                        <Link key={id} href={`/admin/orders/${id}`} className="mr-2 font-medium text-accent-strong hover:underline">
                          #{id}
                        </Link>
                      ))
                    )}
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{courier.delivered_today}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
