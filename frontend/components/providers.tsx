"use client";

import { SWRConfig } from "swr";

import { swrFetcher } from "@/lib/api";
import { AuthProvider } from "@/lib/auth";
import { CartProvider } from "@/lib/cart";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SWRConfig value={{ fetcher: swrFetcher }}>
      <AuthProvider>
        <CartProvider>{children}</CartProvider>
      </AuthProvider>
    </SWRConfig>
  );
}
