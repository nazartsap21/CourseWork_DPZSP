import type { Metadata } from "next";

import { OrderHistory } from "@/components/account/order-history";

export const metadata: Metadata = { title: "My orders · Forkful" };

export default function OrdersPage() {
  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-4 pb-16 pt-8 sm:px-6">
      <h1 className="mb-6 font-serif text-4xl tracking-tight text-ink">My orders</h1>
      <OrderHistory />
    </main>
  );
}
