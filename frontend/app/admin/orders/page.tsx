import type { Metadata } from "next";

import { OrdersBoard } from "@/components/admin/orders-board";

export const metadata: Metadata = { title: "Orders · Admin · Forkful" };

export default function AdminOrdersBoardPage() {
  return <OrdersBoard />;
}
