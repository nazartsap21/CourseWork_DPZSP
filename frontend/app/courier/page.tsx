import type { Metadata } from "next";

import { CourierView } from "@/components/courier/courier-view";

export const metadata: Metadata = { title: "Deliveries · Forkful" };

export default function CourierPage() {
  return <CourierView />;
}
