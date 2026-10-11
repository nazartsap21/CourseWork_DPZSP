"use client";

import { SWRConfig } from "swr";

import { swrFetcher } from "@/lib/api";
import { AuthProvider } from "@/lib/auth";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SWRConfig value={{ fetcher: swrFetcher }}>
      <AuthProvider>{children}</AuthProvider>
    </SWRConfig>
  );
}
