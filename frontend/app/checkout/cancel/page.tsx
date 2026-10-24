import type { Metadata } from "next";
import { Suspense } from "react";

import { PaymentCancelled } from "@/components/payments/payment-cancelled";

export const metadata: Metadata = { title: "Payment cancelled · Forkful" };

export default function PaymentCancelledPage() {
  return (
    // Reads the provider's query parameters with useSearchParams, which needs Suspense.
    <Suspense fallback={<main className="flex-1" aria-busy />}>
      <PaymentCancelled />
    </Suspense>
  );
}
