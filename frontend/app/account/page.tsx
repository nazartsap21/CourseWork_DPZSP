import type { Metadata } from "next";

import { AccountView } from "@/components/account/account-view";

export const metadata: Metadata = { title: "Account · Forkful" };

export default function AccountPage() {
  return <AccountView />;
}
