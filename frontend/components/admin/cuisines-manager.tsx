"use client";

import { Trash2 } from "lucide-react";
import { useState } from "react";
import useSWR from "swr";

import { api } from "@/lib/api";
import { pluralize } from "@/lib/format";
import { useAsyncAction } from "@/lib/use-async-action";
import type { AdminCuisine } from "@/types/admin";

function CuisineRow({ cuisine, onChanged }: { cuisine: AdminCuisine; onChanged: () => Promise<unknown> }) {
  const [name, setName] = useState(cuisine.name);
  const action = useAsyncAction();
  const changed = name.trim() !== cuisine.name;

  return (
    <li className="flex flex-wrap items-center gap-3 px-4 py-2.5 text-sm">
      <input
        value={name}
        onChange={(e) => setName(e.target.value)}
        aria-label={`Name of ${cuisine.name}`}
        className="min-w-0 flex-1 basis-40 rounded-lg border border-transparent bg-transparent px-2 py-1 text-ink outline-none hover:border-line focus:border-accent focus:bg-card"
      />
      <span className="text-xs text-muted-ink">{pluralize(cuisine.restaurant_count, "restaurant", "restaurants")}</span>
      {changed && (
        <button
          type="button"
          disabled={action.pending}
          onClick={() => void action.run(() => api.patch(`/admin/cuisines/${cuisine.id}`, { name })).then(onChanged)}
          className="rounded-full bg-accent px-3 py-1 text-xs font-semibold text-white disabled:opacity-50"
        >
          Rename
        </button>
      )}
      <button
        type="button"
        disabled={action.pending || cuisine.restaurant_count > 0}
        title={cuisine.restaurant_count > 0 ? "Used by restaurants" : undefined}
        aria-label={`Delete ${cuisine.name}`}
        onClick={() => void action.run(() => api.delete(`/admin/cuisines/${cuisine.id}`)).then(onChanged)}
        className="rounded-full p-1.5 text-muted-ink hover:bg-surface hover:text-accent-strong disabled:opacity-30"
      >
        <Trash2 aria-hidden className="h-4 w-4" />
      </button>
      {action.error && (
        <p role="alert" className="w-full px-2 text-xs text-accent-strong">
          {action.error}
        </p>
      )}
    </li>
  );
}

export function CuisinesManager() {
  const { data, mutate } = useSWR<{ items: AdminCuisine[] }>("/admin/cuisines");
  const [name, setName] = useState("");
  const add = useAsyncAction();

  return (
    <div className="max-w-xl">
      <h1 className="font-serif text-3xl text-ink">Cuisines</h1>
      <p className="mt-1 text-sm text-muted-ink">Used for catalog filters. A cuisine can be deleted once no restaurant uses it.</p>

      <form
        className="mt-5 flex gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          void add.run(() => api.post("/admin/cuisines", { name })).then(async (created) => {
            if (created) {
              setName("");
              await mutate();
            }
          });
        }}
      >
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="New cuisine, e.g. Mexican"
          aria-label="New cuisine"
          className="min-w-0 flex-1 rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink outline-none focus:border-accent"
        />
        <button type="submit" disabled={add.pending || name.trim().length < 2} className="rounded-full bg-accent px-4 py-2 text-sm font-semibold text-white hover:bg-accent-strong disabled:opacity-50">
          Add
        </button>
      </form>
      {add.error && (
        <p role="alert" className="mt-2 text-sm text-accent-strong">
          {add.fieldErrors.name ?? add.error}
        </p>
      )}

      {!data ? (
        <div className="mt-5 h-48 animate-pulse rounded-xl bg-surface" aria-busy />
      ) : (
        <ul className="mt-5 divide-y divide-line rounded-xl border border-line bg-card">
          {data.items.map((cuisine) => (
            <CuisineRow key={`${cuisine.id}-${cuisine.name}`} cuisine={cuisine} onChanged={() => mutate()} />
          ))}
        </ul>
      )}
    </div>
  );
}
