import type { Metadata } from "next";

import { FavoritesView } from "@/components/account/favorites-view";

export const metadata: Metadata = { title: "Favorites · Forkful" };

export default function FavoritesPage() {
  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-4 pb-16 pt-8 sm:px-6 lg:px-8">
      <h1 className="mb-6 font-serif text-4xl tracking-tight text-ink">Favorites</h1>
      <FavoritesView />
    </main>
  );
}
