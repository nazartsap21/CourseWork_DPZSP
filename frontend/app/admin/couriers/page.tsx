import type { Metadata } from "next";

import { CouriersManager } from "@/components/admin/couriers-manager";

export const metadata: Metadata = { title: "Couriers · Admin · Forkful" };

export default function AdminCouriersManagerPage() {
  return <CouriersManager />;
}
