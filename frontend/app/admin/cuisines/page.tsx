import type { Metadata } from "next";

import { CuisinesManager } from "@/components/admin/cuisines-manager";

export const metadata: Metadata = { title: "Cuisines · Admin · Forkful" };

export default function AdminCuisinesPage() {
  return <CuisinesManager />;
}
