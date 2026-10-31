import type { Metadata } from "next";

import { PromotionsForm } from "@/components/admin/promotions-form";

export const metadata: Metadata = { title: "Promotions · Admin · Forkful" };

export default function AdminPromotionsFormPage() {
  return <PromotionsForm />;
}
