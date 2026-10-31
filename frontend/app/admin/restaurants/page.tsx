import type { Metadata } from "next";

import { RestaurantsTable } from "@/components/admin/restaurants-table";

export const metadata: Metadata = { title: "Restaurants · Admin · Forkful" };

export default function AdminRestaurantsPage() {
  return <RestaurantsTable />;
}
