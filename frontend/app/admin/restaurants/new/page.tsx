import type { Metadata } from "next";
import Link from "next/link";

import { RestaurantForm } from "@/components/admin/restaurant-form";

export const metadata: Metadata = { title: "New restaurant · Admin · Forkful" };

export default function NewRestaurantPage() {
  return (
    <div className="max-w-3xl">
      <Link href="/admin/restaurants" className="text-sm text-muted-ink hover:text-ink">
        ← Restaurants
      </Link>
      <h1 className="mt-2 font-serif text-3xl text-ink">New restaurant</h1>
      <p className="mt-1 text-sm text-muted-ink">It stays hidden until you mark it active, so you can add the menu first.</p>
      <div className="mt-6">
        <RestaurantForm />
      </div>
    </div>
  );
}
