"use client";

import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { useState } from "react";
import useSWR, { useSWRConfig } from "swr";

import { FormField } from "@/components/form-field";
import { api } from "@/lib/api";
import { inputToKopiyky, kopiykyToInput } from "@/lib/format";
import { useAsyncAction } from "@/lib/use-async-action";
import type { AdminCuisine, AdminRestaurant, RestaurantPayload } from "@/types/admin";
import type { LatLng } from "@/types/orders";

const LocationPicker = dynamic(() => import("@/components/maps/location-picker"), {
  ssr: false,
  loading: () => <div className="h-full w-full animate-pulse bg-surface" />,
});

function TextArea({ label, value, onChange, error }: { label: string; value: string; onChange: (v: string) => void; error?: string }) {
  return (
    <div>
      <label htmlFor="restaurant-description" className="mb-1.5 block text-sm font-medium text-ink">
        {label}
      </label>
      <textarea
        id="restaurant-description"
        rows={3}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-line bg-card px-3 py-2.5 text-ink outline-none focus:border-accent focus:ring-2 focus:ring-accent/30"
      />
      {error && <p className="mt-1.5 text-sm text-accent-strong">{error}</p>}
    </div>
  );
}

/** Create or edit a restaurant. Money is typed in ₴ and sent as kopiyky. */
export function RestaurantForm({ restaurant }: { restaurant?: AdminRestaurant }) {
  const router = useRouter();
  const { mutate } = useSWRConfig();
  const { data: cuisines } = useSWR<{ items: AdminCuisine[] }>("/admin/cuisines");
  const save = useAsyncAction();
  const remove = useAsyncAction();
  const [saved, setSaved] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const [name, setName] = useState(restaurant?.name ?? "");
  const [description, setDescription] = useState(restaurant?.description ?? "");
  const [address, setAddress] = useState(restaurant?.address ?? "");
  const [point, setPoint] = useState<LatLng | null>(restaurant ? { lat: restaurant.lat, lng: restaurant.lng } : null);
  const [prep, setPrep] = useState(String(restaurant?.avg_prep_minutes ?? 20));
  const [minOrder, setMinOrder] = useState(restaurant ? kopiykyToInput(restaurant.min_order_amount) : "200");
  const [imageUrl, setImageUrl] = useState(restaurant?.image_url ?? "");
  const [cuisineIds, setCuisineIds] = useState<number[]>(restaurant?.cuisines.map((c) => c.id) ?? []);
  const [isActive, setIsActive] = useState(restaurant?.is_active ?? false);
  const [localErrors, setLocalErrors] = useState<Record<string, string>>({});

  const errors = { ...save.fieldErrors, ...localErrors };

  async function submit() {
    const minOrderAmount = inputToKopiyky(minOrder);
    // Checked here so every missing field is reported at once; the API validates again.
    const problems: Record<string, string> = {};
    if (name.trim().length < 2) problems.name = "Enter the restaurant name.";
    if (address.trim().length < 5) problems.address = "Enter the street and building.";
    if (minOrderAmount === null) problems.min_order_amount = "Enter an amount like 250 or 249.50.";
    if (!point) problems.location = "Click the map to set the location.";
    if (cuisineIds.length === 0) problems.cuisine_ids = "Choose at least one cuisine.";
    setLocalErrors(problems);
    setSaved(false);
    if (Object.keys(problems).length > 0 || !point || minOrderAmount === null) return;

    const payload: RestaurantPayload = {
      name,
      description,
      address,
      lat: point.lat,
      lng: point.lng,
      avg_prep_minutes: Number(prep),
      min_order_amount: minOrderAmount,
      image_url: imageUrl.trim() || null,
      is_active: isActive,
      cuisine_ids: cuisineIds,
    };
    const result = await save.run(() =>
      restaurant
        ? api.patch<AdminRestaurant>(`/admin/restaurants/${restaurant.id}`, payload)
        : api.post<AdminRestaurant>("/admin/restaurants", payload),
    );
    if (!result) return;
    if (restaurant) {
      await mutate(`/admin/restaurants/${restaurant.id}`, result, { revalidate: false });
      setSaved(true);
    } else {
      router.push(`/admin/restaurants/${result.id}`);
    }
  }

  async function deleteRestaurant() {
    if (!restaurant) return;
    const done = await remove.run(() => api.delete(`/admin/restaurants/${restaurant.id}`).then(() => true));
    if (done) router.push("/admin/restaurants");
    else setConfirmDelete(false);
  }

  return (
    <form
      noValidate
      className="space-y-6"
      onSubmit={(event) => {
        event.preventDefault();
        void submit();
      }}
    >
      <div className="grid gap-5 md:grid-cols-2">
        <FormField label="Name" value={name} onChange={(e) => setName(e.target.value)} error={errors.name} />
        <FormField label="Address" value={address} onChange={(e) => setAddress(e.target.value)} error={errors.address} placeholder="vul. Virmenska 18, Lviv" />
      </div>
      <TextArea label="Description" value={description} onChange={setDescription} error={errors.description} />

      <div>
        <p className="mb-1.5 text-sm font-medium text-ink">Location</p>
        <div className={`h-64 overflow-hidden rounded-xl border ${errors.location || errors.lat ? "border-accent-strong" : "border-line"}`}>
          <LocationPicker value={point} onChange={setPoint} />
        </div>
        <p className={`mt-1.5 text-xs ${errors.location ? "text-accent-strong" : "text-muted-ink"}`}>
          {errors.location ?? (point ? `${point.lat.toFixed(5)}, ${point.lng.toFixed(5)}` : "Click the map where the restaurant is.")}
        </p>
      </div>

      <div className="grid gap-5 sm:grid-cols-3">
        <FormField label="Prep time, min" type="number" min={5} max={180} value={prep} onChange={(e) => setPrep(e.target.value)} error={errors.avg_prep_minutes} />
        <FormField label="Minimum order, ₴" inputMode="decimal" value={minOrder} onChange={(e) => setMinOrder(e.target.value)} error={errors.min_order_amount} />
        <FormField label="Image URL" value={imageUrl} onChange={(e) => setImageUrl(e.target.value)} error={errors.image_url} placeholder="https://… (optional)" />
      </div>

      <fieldset>
        <legend className="mb-2 text-sm font-medium text-ink">Cuisines</legend>
        <div className="flex flex-wrap gap-2">
          {cuisines?.items.map((cuisine) => {
            const selected = cuisineIds.includes(cuisine.id);
            return (
              <button
                key={cuisine.id}
                type="button"
                aria-pressed={selected}
                onClick={() => setCuisineIds(selected ? cuisineIds.filter((id) => id !== cuisine.id) : [...cuisineIds, cuisine.id])}
                className={`rounded-full border px-3 py-1.5 text-sm transition ${selected ? "border-ink bg-ink text-background" : "border-line bg-card text-ink hover:border-muted-ink/50"}`}
              >
                {cuisine.name}
              </button>
            );
          })}
        </div>
        {errors.cuisine_ids && <p className="mt-1.5 text-sm text-accent-strong">Choose at least one cuisine.</p>}
      </fieldset>

      <label className="inline-flex items-center gap-3 text-sm text-ink">
        <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} className="h-4 w-4 accent-[var(--accent)]" />
        Active: shown in the catalog and taking orders
      </label>

      {save.error && Object.keys(save.fieldErrors).length === 0 && (
        <p role="alert" className="text-sm text-accent-strong">
          {save.error}
        </p>
      )}

      <div className="flex flex-wrap items-center gap-4 border-t border-line pt-5">
        <button
          type="submit"
          disabled={save.pending}
          className="rounded-full bg-accent px-5 py-2.5 text-sm font-semibold text-white hover:bg-accent-strong disabled:opacity-50"
        >
          {save.pending ? "Saving…" : restaurant ? "Save changes" : "Create restaurant"}
        </button>
        {saved && (
          <span role="status" className="text-sm text-sage">
            Saved
          </span>
        )}
        {restaurant &&
          (confirmDelete ? (
            <span className="ml-auto inline-flex items-center gap-2 text-sm">
              Delete for good?
              <button type="button" onClick={() => void deleteRestaurant()} disabled={remove.pending} className="rounded-full bg-accent-strong px-3 py-1.5 font-semibold text-white disabled:opacity-50">
                Delete
              </button>
              <button type="button" onClick={() => setConfirmDelete(false)} className="rounded-full px-3 py-1.5 text-ink hover:bg-surface">
                Keep
              </button>
            </span>
          ) : (
            <button type="button" onClick={() => setConfirmDelete(true)} className="ml-auto text-sm text-muted-ink hover:text-accent-strong">
              Delete restaurant
            </button>
          ))}
      </div>
      {remove.error && (
        <p role="alert" className="text-sm text-accent-strong">
          {remove.error}
        </p>
      )}
    </form>
  );
}
