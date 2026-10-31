import type { Metadata } from "next";

import { LoyaltySettingsForm } from "@/components/admin/loyalty-settings-form";

export const metadata: Metadata = { title: "Loyalty · Admin · Forkful" };

export default function AdminLoyaltySettingsFormPage() {
  return <LoyaltySettingsForm />;
}
