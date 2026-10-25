"use client";

import { Heart } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAuth } from "@/lib/auth";
import { useFavorites } from "@/lib/favorites";
import type { RestaurantSummary } from "@/types/catalog";

const buttonClass =
  "inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition disabled:opacity-50";

export function FavoriteButton({ restaurant }: { restaurant: RestaurantSummary }) {
  const { user, status } = useAuth();
  const pathname = usePathname();
  const favorites = useFavorites();

  if (status === "loading" || (user && user.role !== "customer")) return null;

  if (!user) {
    return (
      <Link
        href={`/login?next=${encodeURIComponent(pathname)}`}
        className={`${buttonClass} border-line text-ink hover:border-muted-ink/50`}
      >
        <Heart aria-hidden className="h-4 w-4" />
        Save
      </Link>
    );
  }

  const saved = favorites.isFavorite(restaurant.id);
  return (
    <button
      type="button"
      onClick={() => void favorites.toggle(restaurant)}
      disabled={favorites.isLoading}
      aria-pressed={saved}
      className={`${buttonClass} ${
        saved ? "border-accent bg-accent/10 text-accent-strong" : "border-line text-ink hover:border-muted-ink/50"
      }`}
    >
      <Heart aria-hidden className={`h-4 w-4 ${saved ? "fill-accent text-accent" : ""}`} />
      {saved ? "Saved" : "Save"}
    </button>
  );
}
