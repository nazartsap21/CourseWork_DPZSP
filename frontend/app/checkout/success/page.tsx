import type { Metadata } from "next";
import { Suspense } from "react";

import { PaymentSuccess } from "@/components/payments/payment-success";

export const metadata: Metadata = { title: "Payment · Forkful" };

export default function PaymentSuccessPage() {
  return (
    // Reads the provider's query parameters with useSearchParams, which needs Suspense.
    <Suspense fallback={<main className="flex-1" aria-busy />}>
      <PaymentSuccess />
    </Suspense>
  );
}
