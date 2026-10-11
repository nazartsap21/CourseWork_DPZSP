import { Suspense } from "react";

import { CatalogView } from "@/components/catalog/catalog-view";
import { RestaurantCardSkeleton } from "@/components/catalog/restaurant-card";

export default function CatalogPage() {
  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-4 pb-16 pt-8 sm:px-6 lg:px-8 lg:pt-10">
      <div className="mb-8 border-b border-line pb-6">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-sage">Lviv · delivery and pickup</p>
        <h1 className="mt-2 font-serif text-4xl tracking-tight text-ink sm:text-5xl">What are we eating today?</h1>
      </div>
      {/* Filters are read from the URL with useSearchParams, which needs Suspense. */}
      <Suspense
        fallback={
          <div className="grid gap-x-6 gap-y-10 sm:grid-cols-2 lg:ml-[17.5rem] xl:grid-cols-3">
            {Array.from({ length: 6 }, (_, i) => (
              <RestaurantCardSkeleton key={i} />
            ))}
          </div>
        }
      >
        <CatalogView />
      </Suspense>
    </main>
  );
}
