"use client";

import { Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import useSWR from "swr";

import { FormField } from "@/components/form-field";
import { api } from "@/lib/api";
import { formatPrice, inputToKopiyky, kopiykyToInput } from "@/lib/format";
import { useAsyncAction } from "@/lib/use-async-action";
import type { DishPayload } from "@/types/admin";
import type { Dish } from "@/types/catalog";

function DishForm({
  dish,
  categories,
  onSubmit,
  onCancel,
  pending,
  fieldErrors,
}: {
  dish?: Dish;
  categories: string[];
  onSubmit: (payload: DishPayload) => void;
  onCancel: () => void;
  pending: boolean;
  fieldErrors: Record<string, string>;
}) {
  const [name, setName] = useState(dish?.name ?? "");
  const [category, setCategory] = useState(dish?.category ?? categories[0] ?? "");
  const [price, setPrice] = useState(dish ? kopiykyToInput(dish.price) : "");
  const [description, setDescription] = useState(dish?.description ?? "");
  const [priceError, setPriceError] = useState<string | null>(null);
  const listId = `categories-${dish?.id ?? "new"}`;

  return (
    <form
      noValidate
      className="space-y-4 rounded-xl border border-line bg-card p-4"
      onSubmit={(event) => {
        event.preventDefault();
        const kopiyky = inputToKopiyky(price);
        if (kopiyky === null || kopiyky <= 0) {
          setPriceError("Enter a price like 215 or 89.50.");
          return;
        }
        setPriceError(null);
        onSubmit({ name, category, price: kopiyky, description, is_available: dish?.is_available ?? true, image_url: dish?.image_url ?? null });
      }}
    >
      <div className="grid gap-4 sm:grid-cols-[1fr_12rem_8rem]">
        <FormField label="Dish" value={name} onChange={(e) => setName(e.target.value)} error={fieldErrors.name} />
        <FormField label="Category" value={category} onChange={(e) => setCategory(e.target.value)} error={fieldErrors.category} list={listId} placeholder="Pizza" />
        <FormField label="Price, ₴" inputMode="decimal" value={price} onChange={(e) => setPrice(e.target.value)} error={priceError ?? fieldErrors.price} />
      </div>
      <datalist id={listId}>
        {categories.map((c) => (
          <option key={c} value={c} />
        ))}
      </datalist>
      <FormField label="Description" value={description} onChange={(e) => setDescription(e.target.value)} error={fieldErrors.description} placeholder="Tomatoes, mozzarella, basil." />
      <div className="flex gap-2">
        <button type="submit" disabled={pending} className="rounded-full bg-accent px-4 py-2 text-sm font-semibold text-white hover:bg-accent-strong disabled:opacity-50">
          {pending ? "Saving…" : dish ? "Save dish" : "Add dish"}
        </button>
        <button type="button" onClick={onCancel} className="rounded-full px-4 py-2 text-sm text-ink hover:bg-surface">
          Cancel
        </button>
      </div>
    </form>
  );
}

/** The restaurant's menu for admins: all dishes, including unavailable ones, grouped by category. */
export function DishesManager({ restaurantId }: { restaurantId: number }) {
  const key = `/admin/restaurants/${restaurantId}/dishes`;
  const { data, mutate } = useSWR<{ items: Dish[] }>(key);
  const action = useAsyncAction();
  const [editing, setEditing] = useState<number | "new" | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null);

  const dishes = data?.items ?? [];
  const categories = [...new Set(dishes.map((d) => d.category))];
  const grouped = categories.map((category) => ({ category, dishes: dishes.filter((d) => d.category === category) }));

  async function save(payload: DishPayload, dish?: Dish) {
    const result = await action.run(() =>
      dish ? api.patch<Dish>(`/admin/dishes/${dish.id}`, payload) : api.post<Dish>(`/admin/restaurants/${restaurantId}/dishes`, payload),
    );
    if (result) {
      setEditing(null);
      await mutate();
    }
  }

  async function toggleAvailable(dish: Dish) {
    await action.run(() => api.patch(`/admin/dishes/${dish.id}`, { is_available: !dish.is_available }));
    await mutate();
  }

  async function remove(dish: Dish) {
    await action.run(() => api.delete(`/admin/dishes/${dish.id}`));
    setConfirmDelete(null);
    await mutate();
  }

  return (
    <section aria-labelledby="dishes-title">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 id="dishes-title" className="font-serif text-2xl text-ink">
          Menu <span className="text-base font-normal text-muted-ink">{dishes.length}</span>
        </h2>
        {editing !== "new" && (
          <button
            type="button"
            onClick={() => setEditing("new")}
            className="inline-flex items-center gap-1.5 rounded-full border border-ink px-4 py-2 text-sm font-semibold text-ink hover:bg-ink hover:text-background"
          >
            <Plus aria-hidden className="h-4 w-4" />
            Add dish
          </button>
        )}
      </div>

      {editing === "new" && (
        <div className="mt-4">
          <DishForm categories={categories} onSubmit={(p) => void save(p)} onCancel={() => setEditing(null)} pending={action.pending} fieldErrors={action.fieldErrors} />
        </div>
      )}
      {action.error && Object.keys(action.fieldErrors).length === 0 && (
        <p role="alert" className="mt-3 text-sm text-accent-strong">
          {action.error}
        </p>
      )}

      {!data ? (
        <div className="mt-4 h-40 animate-pulse rounded-xl bg-surface" aria-busy />
      ) : dishes.length === 0 ? (
        <p className="mt-4 rounded-xl border border-dashed border-line px-5 py-8 text-center text-sm text-muted-ink">
          No dishes yet. Add the first one to open the menu.
        </p>
      ) : (
        <div className="mt-4 space-y-6">
          {grouped.map(({ category, dishes: group }) => (
            <div key={category}>
              <h3 className="font-sans text-xs font-semibold uppercase tracking-[0.18em] text-sage">{category}</h3>
              <ul className="mt-2 divide-y divide-line rounded-xl border border-line bg-card">
                {group.map((dish) =>
                  editing === dish.id ? (
                    <li key={dish.id} className="p-2">
                      <DishForm dish={dish} categories={categories} onSubmit={(p) => void save(p, dish)} onCancel={() => setEditing(null)} pending={action.pending} fieldErrors={action.fieldErrors} />
                    </li>
                  ) : (
                    <li key={dish.id} className="flex flex-wrap items-center gap-3 px-4 py-2.5 text-sm">
                      <span className={`min-w-0 flex-1 basis-48 ${dish.is_available ? "text-ink" : "text-muted-ink line-through"}`}>
                        {dish.name}
                        {dish.description && <span className="block truncate text-xs text-muted-ink no-underline">{dish.description}</span>}
                      </span>
                      <span className="w-20 text-right tabular-nums text-ink">{formatPrice(dish.price)}</span>
                      <button
                        type="button"
                        role="switch"
                        aria-checked={dish.is_available}
                        aria-label={`${dish.name} available`}
                        onClick={() => void toggleAvailable(dish)}
                        className={`rounded-full px-2.5 py-1 text-xs font-medium ${dish.is_available ? "bg-sage text-white" : "bg-surface text-muted-ink"}`}
                      >
                        {dish.is_available ? "Available" : "Sold out"}
                      </button>
                      <button type="button" onClick={() => setEditing(dish.id)} aria-label={`Edit ${dish.name}`} className="rounded-full p-1.5 text-muted-ink hover:bg-surface hover:text-ink">
                        <Pencil aria-hidden className="h-4 w-4" />
                      </button>
                      {confirmDelete === dish.id ? (
                        <span className="inline-flex items-center gap-1">
                          <button type="button" onClick={() => void remove(dish)} className="rounded-full bg-accent-strong px-2.5 py-1 text-xs font-semibold text-white">
                            Delete
                          </button>
                          <button type="button" onClick={() => setConfirmDelete(null)} className="rounded-full px-2.5 py-1 text-xs text-ink hover:bg-surface">
                            Keep
                          </button>
                        </span>
                      ) : (
                        <button type="button" onClick={() => setConfirmDelete(dish.id)} aria-label={`Delete ${dish.name}`} className="rounded-full p-1.5 text-muted-ink hover:bg-surface hover:text-accent-strong">
                          <Trash2 aria-hidden className="h-4 w-4" />
                        </button>
                      )}
                    </li>
                  ),
                )}
              </ul>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
